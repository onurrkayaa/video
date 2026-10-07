// medya-apple — stüdyonun Apple çerçeveleri aracı (VideoToolbox, Vision, SoundAnalysis).
// Modeller macOS'un içinde gelir: indirme yok, hesap yok, Neural Engine/GPU hızlandırmalı.
//
// Derleme (Xcode lisansı gerekmez, Command Line Tools yeter):
//   DEVELOPER_DIR=/Library/Developer/CommandLineTools swiftc -O -parse-as-library -swift-version 5 \
//     sistem/apple/medya-apple.swift -o arac/medya-apple
//
// Komutlar:
//   yavaslat <girdi> <cikti.mov|mp4> <kat 2..8> [--bas sn] [--sure sn] [--kodek prores|hevc|h264] [--kalite 0..1]
//       ML ara kare üretimiyle ağır çekim (VTFrameRateConversion). Her kare çiftinin arasına kat-1 kare
//       üretir; çıktı aynı fps'te oynar, dolayısıyla süre kat katına çıkar. Ses yazılmaz. Girdi SABİT kare
//       hızında ve yinelenen karesiz olmalı (medya yavaslat bunu kendisi hazırlar).
//   analiz <video|resim> <cikti.json> [--aralik sn]
//       Örneklenen her karede: estetik puan, yüzler (+yakalama kalitesi), insanlar, dikkat çeken bölge,
//       sahne etiketleri, bir önceki örneğe görsel uzaklık. Kutular sol-üst kökenli, 0..1 normalize.
//   ses-olay <ses.wav> <cikti.json> [--pencere sn]
//       Gömülü ses sınıflandırıcısı (303 sınıf): kahkaha, alkış, konuşma, şarkı, müzik…
//   arkaplan-sil <resim> <cikti.png> [--maske maske.png] [--kirp evet]
//       Vision ön plan örnek maskesiyle arka planı siler (şeffaf PNG). Saç/tüy/cam gibi zor kenarlarda
//       gorsel-uretim becerisindeki daha ağır yöntemlere bak.
//   yetenek
//       Bu Mac'te hangi VideoToolbox işlemcilerinin desteklendiğini JSON olarak yazar.
//
// Denenip ALINMAYAN: VTSuperResolutionScaler ile durağan görüntü büyütme (2026-10-05). Bu Mac yalnız 4x destekliyor;
// görüntü modeli indirme istiyor, video modeli doğrusal girdiyle gölgeleri koyulaştırdı (35→20) ve PSNR'da bikübikten
// kötü çıktı (26,5 dB'ye 29,4 dB); sRGB/709 girdide çıktı tümüyle siyah. Büyütme için gorsel-uretim becerisine bak.

import AVFoundation
import CoreImage
import CoreMedia
import CoreVideo
import Foundation
import SoundAnalysis
import Vision
import VideoToolbox

struct Hata: Error, CustomStringConvertible {
    let description: String
    init(_ d: String) { description = d }
}

struct Arg {
    var konum: [String] = []
    var secenek: [String: String] = [:]
    init(_ a: [String]) {
        var i = 0
        while i < a.count {
            if a[i].hasPrefix("--"), i + 1 < a.count { secenek[a[i]] = a[i + 1]; i += 2 } else { konum.append(a[i]); i += 1 }
        }
    }
    func pos(_ i: Int) throws -> String {
        guard i < konum.count else { throw Hata("eksik argüman (\(i + 1). konum)") }
        return konum[i]
    }
    func sayi(_ k: String) -> Double? { secenek[k].flatMap(Double.init) }
}

func jsonYaz(_ nesne: Any, _ yol: String) throws {
    let veri = try JSONSerialization.data(withJSONObject: nesne, options: [.prettyPrinted, .sortedKeys])
    try veri.write(to: URL(fileURLWithPath: yol))
}

func yuvarla(_ x: Double, _ b: Int = 4) -> Double { let p = pow(10.0, Double(b)); return (x * p).rounded() / p }

// Vision kutusu (sol-alt köken) → sol-üst köken [x, y, w, h]
func kutu(_ r: NormalizedRect) -> [Double] {
    let c = r.cgRect
    return [yuvarla(c.origin.x), yuvarla(1 - c.origin.y - c.height), yuvarla(c.width), yuvarla(c.height)]
}

// MARK: - yavaslat

func pikselTamponu(_ oz: [String: Any], _ w: Int, _ h: Int) throws -> CVPixelBuffer {
    var at = oz
    var bicim: OSType = kCVPixelFormatType_64RGBAHalf
    if let n = oz[kCVPixelBufferPixelFormatTypeKey as String] as? NSNumber { bicim = n.uint32Value }
    else if let a = oz[kCVPixelBufferPixelFormatTypeKey as String] as? [NSNumber], let n = a.first { bicim = n.uint32Value }
    at.removeValue(forKey: kCVPixelBufferPixelFormatTypeKey as String)
    at.removeValue(forKey: kCVPixelBufferWidthKey as String)
    at.removeValue(forKey: kCVPixelBufferHeightKey as String)
    if at[kCVPixelBufferIOSurfacePropertiesKey as String] == nil { at[kCVPixelBufferIOSurfacePropertiesKey as String] = [String: Any]() }
    var pb: CVPixelBuffer?
    let st = CVPixelBufferCreate(kCFAllocatorDefault, w, h, bicim, at as CFDictionary, &pb)
    guard st == kCVReturnSuccess, let p = pb else { throw Hata("CVPixelBufferCreate \(st)") }
    return p
}

func yavaslat(_ a: Arg) async throws {
    let girdi = URL(fileURLWithPath: try a.pos(0)), cikti = URL(fileURLWithPath: try a.pos(1))
    guard let kat = Int(try a.pos(2)), (2...8).contains(kat) else { throw Hata("kat 2..8 olmalı") }
    let kalite = a.sayi("--kalite") ?? 0.9
    guard VTFrameRateConversionConfiguration.isSupported else { throw Hata("VTFrameRateConversion bu Mac'te desteklenmiyor") }

    let varlik = AVURLAsset(url: girdi)
    guard let iz = try await varlik.loadTracks(withMediaType: .video).first else { throw Hata("video izi yok") }
    let (fpsF, donus) = try await iz.load(.nominalFrameRate, .preferredTransform)
    let fps = Double(fpsF)
    guard fps > 0 else { throw Hata("kare hızı okunamadı") }

    let okuyucu = try AVAssetReader(asset: varlik)
    if let bas = a.sayi("--bas") {
        let sure = a.sayi("--sure") ?? 1e7
        okuyucu.timeRange = CMTimeRange(start: CMTime(seconds: bas, preferredTimescale: 60000),
                                        duration: CMTime(seconds: sure, preferredTimescale: 60000))
    }
    let cikis = AVAssetReaderTrackOutput(track: iz, outputSettings: [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA])
    cikis.alwaysCopiesSampleData = false
    okuyucu.add(cikis)

    guard okuyucu.startReading() else { throw Hata("okuyucu: \(okuyucu.error.map { "\($0)" } ?? "?")") }
    // boyut ilk çözülen kareden alınır (naturalSize piksel en-boy oranını uygular, gerçek tampon boyutu değildir)
    guard let ilk = cikis.copyNextSampleBuffer(), let ilkPB = CMSampleBufferGetImageBuffer(ilk) else { throw Hata("kare okunamadı") }
    let w = CVPixelBufferGetWidth(ilkPB), h = CVPixelBufferGetHeight(ilkPB)

    try? FileManager.default.removeItem(at: cikti)
    let tur: AVFileType = cikti.pathExtension.lowercased() == "mov" ? .mov : .mp4
    let yazici = try AVAssetWriter(outputURL: cikti, fileType: tur)
    // kodek: prores (varsayılan; ProRes 422 HQ, ara dosya için görsel kayıpsız) | hevc | h264
    let kodek = a.secenek["--kodek"] ?? (tur == .mov ? "prores" : "hevc")
    var ayar: [String: Any] = [
        AVVideoWidthKey: w, AVVideoHeightKey: h,
        AVVideoColorPropertiesKey: [AVVideoColorPrimariesKey: AVVideoColorPrimaries_ITU_R_709_2,
                                    AVVideoTransferFunctionKey: AVVideoTransferFunction_ITU_R_709_2,
                                    AVVideoYCbCrMatrixKey: AVVideoYCbCrMatrix_ITU_R_709_2],
    ]
    switch kodek {
    case "prores":
        guard tur == .mov else { throw Hata("ProRes yalnız .mov çıktıyla yazılır") }
        ayar[AVVideoCodecKey] = AVVideoCodecType.proRes422HQ
    case "h264":
        ayar[AVVideoCodecKey] = AVVideoCodecType.h264
        ayar[AVVideoCompressionPropertiesKey] = [AVVideoQualityKey: kalite, AVVideoExpectedSourceFrameRateKey: Int(fps.rounded())]
    default:
        ayar[AVVideoCodecKey] = AVVideoCodecType.hevc
        ayar[AVVideoCompressionPropertiesKey] = [AVVideoQualityKey: kalite, AVVideoExpectedSourceFrameRateKey: Int(fps.rounded())]
    }
    let giris = AVAssetWriterInput(mediaType: .video, outputSettings: ayar)
    giris.transform = donus
    giris.expectsMediaDataInRealTime = false
    let uyarlayici = AVAssetWriterInputPixelBufferAdaptor(assetWriterInput: giris, sourcePixelBufferAttributes: [
        kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA,
        kCVPixelBufferWidthKey as String: w, kCVPixelBufferHeightKey as String: h,
        kCVPixelBufferIOSurfacePropertiesKey as String: [String: Any](),
    ])
    yazici.add(giris)
    guard yazici.startWriting() else { throw Hata("yazıcı: \(yazici.error.map { "\($0)" } ?? "?")") }
    yazici.startSession(atSourceTime: .zero)

    guard let cfg = VTFrameRateConversionConfiguration(frameWidth: w, frameHeight: h, usePrecomputedFlow: false,
                                                       qualityPrioritization: .quality,
                                                       revision: VTFrameRateConversionConfiguration.defaultRevision)
    else { throw Hata("FRC yapılandırması kurulamadı (\(w)x\(h)); boyut destek dışı olabilir") }
    let islemci = VTFrameProcessor()
    try islemci.startSession(configuration: cfg)
    defer { islemci.endSession() }

    let dogrusal = CGColorSpace(name: CGColorSpace.extendedLinearSRGB)!, srgb = CGColorSpace(name: CGColorSpace.sRGB)!
    let ciz = CIContext(options: [.workingColorSpace: dogrusal, .cacheIntermediates: false])
    let alan = CGRect(x: 0, y: 0, width: w, height: h)
    var kaynakA = try pikselTamponu(cfg.sourcePixelBufferAttributes, w, h)
    var kaynakB = try pikselTamponu(cfg.sourcePixelBufferAttributes, w, h)
    let fazlar: [Float] = (1..<kat).map { Float($0) / Float(kat) }
    let hedefler = try fazlar.map { _ in try pikselTamponu(cfg.destinationPixelBufferAttributes, w, h) }

    let olcek: Int32 = 60000
    let adim = Int64((Double(olcek) / fps).rounded())
    var n: Int64 = 0
    func ekle(_ pb: CVPixelBuffer) async throws {
        while !giris.isReadyForMoreMediaData { try await Task.sleep(nanoseconds: 2_000_000) }
        guard uyarlayici.append(pb, withPresentationTime: CMTime(value: n * adim, timescale: olcek)) else {
            throw Hata("kare eklenemedi: \(yazici.error.map { "\($0)" } ?? "?")")
        }
        n += 1
    }
    func havuzTamponu() throws -> CVPixelBuffer {
        guard let havuz = uyarlayici.pixelBufferPool else { throw Hata("tampon havuzu yok") }
        var pb: CVPixelBuffer?
        CVPixelBufferPoolCreatePixelBuffer(nil, havuz, &pb)
        guard let p = pb else { throw Hata("havuz tamponu alınamadı") }
        return p
    }

    let zs = Int32(Int(fps.rounded()) * kat)          // FRC zaman damgaları: çıktı karesi biriminde
    var onceki: CMSampleBuffer? = ilk
    var j: Int64 = 0
    var sureler: [Double] = []
    var oncekiCizildi = false
    while let ornek = cikis.copyNextSampleBuffer() {
        guard let pb = CMSampleBufferGetImageBuffer(ornek) else { continue }
        if let o = onceki, let opb = CMSampleBufferGetImageBuffer(o) {
            try await ekle(opb)                                       // özgün kare, dokunulmadan
            if !oncekiCizildi {
                ciz.render(CIImage(cvPixelBuffer: opb, options: [.colorSpace: srgb]), to: kaynakA, bounds: alan, colorSpace: dogrusal)
            }
            ciz.render(CIImage(cvPixelBuffer: pb, options: [.colorSpace: srgb]), to: kaynakB, bounds: alan, colorSpace: dogrusal)
            let k = Int64(kat)
            let s = VTFrameProcessorFrame(buffer: kaynakA, presentationTimeStamp: CMTime(value: j * k, timescale: zs))!
            let sonraki = VTFrameProcessorFrame(buffer: kaynakB, presentationTimeStamp: CMTime(value: (j + 1) * k, timescale: zs))!
            let hk = zip(fazlar.indices, hedefler).map { (i, d) in
                VTFrameProcessorFrame(buffer: d, presentationTimeStamp: CMTime(value: j * k + Int64(i + 1), timescale: zs))!
            }
            guard let prm = VTFrameRateConversionParameters(sourceFrame: s, nextFrame: sonraki, opticalFlow: nil,
                                                            interpolationPhase: fazlar, submissionMode: .sequential,
                                                            destinationFrames: hk)
            else { throw Hata("FRC parametreleri kurulamadı") }
            let t0 = Date()
            _ = try await islemci.process(parameters: prm)
            sureler.append(Date().timeIntervalSince(t0))
            for d in hedefler {
                let cikisPB = try havuzTamponu()
                ciz.render(CIImage(cvPixelBuffer: d, options: [.colorSpace: dogrusal]), to: cikisPB, bounds: alan, colorSpace: srgb)
                try await ekle(cikisPB)
            }
            swap(&kaynakA, &kaynakB)                                  // B bir sonraki çiftin A'sı (yeniden çizilmez)
            oncekiCizildi = true
            j += 1
        }
        onceki = ornek
    }
    if let o = onceki, let opb = CMSampleBufferGetImageBuffer(o) { try await ekle(opb) }
    giris.markAsFinished()
    await yazici.finishWriting()
    if yazici.status != .completed { throw Hata("yazma başarısız: \(yazici.error.map { "\($0)" } ?? "?")") }
    let sirali = sureler.sorted()
    let medyan = sirali.isEmpty ? 0 : sirali[sirali.count / 2]
    let rapor: [String: Any] = ["kare": n, "cift": j, "kat": kat, "fps": fps, "boyut": "\(w)x\(h)",
                                "cift_basina_ms_medyan": yuvarla(medyan * 1000, 1), "cikti": cikti.path]
    let veri = try JSONSerialization.data(withJSONObject: rapor, options: [.sortedKeys])
    print(String(data: veri, encoding: .utf8)!)
}

// MARK: - analiz

func resimMi(_ u: URL) -> Bool { ["jpg", "jpeg", "png", "heic", "heif", "tif", "tiff", "webp", "dng"].contains(u.pathExtension.lowercased()) }

func kareAnaliz(_ cg: CGImage, onceki: FeaturePrintObservation?) async -> ([String: Any], FeaturePrintObservation?) {
    let el = ImageRequestHandler(cg)
    var r: [String: Any] = [:]
    if let e = try? await el.perform(CalculateImageAestheticsScoresRequest()) {
        r["estetik"] = yuvarla(Double(e.overallScore), 3); r["fayda"] = e.isUtility
    }
    if let yuzler = try? await el.perform(DetectFaceCaptureQualityRequest()) {
        r["yuzler"] = yuzler.map { y -> [String: Any] in
            var d: [String: Any] = ["kutu": kutu(y.boundingBox), "guven": yuvarla(Double(y.confidence), 3)]
            if let q = y.captureQuality { d["kalite"] = yuvarla(Double(q.score), 3) }
            return d
        }
    }
    var insan = DetectHumanRectanglesRequest()
    insan.upperBodyOnly = false
    if let ins = try? await el.perform(insan) { r["insanlar"] = ins.map { kutu($0.boundingBox) } }
    if let s = try? await el.perform(GenerateAttentionBasedSaliencyImageRequest()) {
        r["ilgi"] = s.salientObjects.map { kutu($0.boundingBox) }
    }
    if let c = try? await el.perform(ClassifyImageRequest()) {
        r["etiketler"] = c.filter { $0.confidence > 0.15 }.sorted { $0.confidence > $1.confidence }.prefix(6)
            .map { [$0.identifier, yuvarla(Double($0.confidence), 3)] as [Any] }
    }
    var fp: FeaturePrintObservation? = nil
    if let f = try? await el.perform(GenerateImageFeaturePrintRequest()) {
        fp = f
        if let o = onceki, let d = try? f.distance(to: o) { r["fark_onceki"] = yuvarla(d, 4) }
    }
    return (r, fp)
}

func analiz(_ a: Arg) async throws {
    let girdi = URL(fileURLWithPath: try a.pos(0)), cikti = try a.pos(1)
    var kareler: [[String: Any]] = []
    var boyutBilgi = ""
    if resimMi(girdi) {
        guard let kaynak = CGImageSourceCreateWithURL(girdi as CFURL, nil),
              let cg = CGImageSourceCreateImageAtIndex(kaynak, 0, [kCGImageSourceShouldCache: false] as CFDictionary)
        else { throw Hata("resim açılamadı") }
        boyutBilgi = "\(cg.width)x\(cg.height)"
        var (r, _) = await kareAnaliz(cg, onceki: nil)
        r["t"] = 0.0
        kareler.append(r)
    } else {
        let varlik = AVURLAsset(url: girdi)
        let sure = try await varlik.load(.duration).seconds
        let uretec = AVAssetImageGenerator(asset: varlik)
        uretec.appliesPreferredTrackTransform = true
        uretec.requestedTimeToleranceBefore = .zero
        uretec.requestedTimeToleranceAfter = .zero
        uretec.maximumSize = CGSize(width: 1024, height: 1024)
        let aralik = a.sayi("--aralik") ?? 0.5
        var t = min(aralik / 2, max(0, sure - 0.05))
        var onceki: FeaturePrintObservation? = nil
        while t < sure {
            let (cg, _) = try await uretec.image(at: CMTime(seconds: t, preferredTimescale: 60000))
            if boyutBilgi.isEmpty { boyutBilgi = "\(cg.width)x\(cg.height)" }
            var (r, fp) = await kareAnaliz(cg, onceki: onceki)
            onceki = fp ?? onceki
            r["t"] = yuvarla(t, 3)
            kareler.append(r)
            t += aralik
        }
    }
    try jsonYaz(["kaynak": girdi.path, "analiz_boyutu": boyutBilgi, "kareler": kareler], cikti)
    print("\(kareler.count) kare analiz edildi → \(cikti)")
}

// MARK: - ses-olay

final class SesGozlemci: NSObject, SNResultsObserving {
    var pencereler: [[String: Any]] = []
    var hata: Error?
    func request(_ request: SNRequest, didProduce result: SNResult) {
        guard let c = result as? SNClassificationResult else { return }
        let ust = c.classifications.prefix(6).filter { $0.confidence > 0.05 }.map { [$0.identifier, yuvarla($0.confidence, 3)] as [Any] }
        pencereler.append(["bas": yuvarla(c.timeRange.start.seconds, 3),
                           "son": yuvarla(c.timeRange.start.seconds + c.timeRange.duration.seconds, 3), "siniflar": ust])
    }
    func request(_ request: SNRequest, didFailWithError error: Error) { hata = error }
    func requestDidComplete(_ request: SNRequest) {}
}

func sesOlay(_ a: Arg) throws {
    let girdi = URL(fileURLWithPath: try a.pos(0)), cikti = try a.pos(1)
    let analizci = try SNAudioFileAnalyzer(url: girdi)
    let istek = try SNClassifySoundRequest(classifierIdentifier: .version1)
    istek.windowDuration = CMTime(seconds: a.sayi("--pencere") ?? 1.0, preferredTimescale: 48000)
    istek.overlapFactor = 0.5
    let g = SesGozlemci()
    try analizci.add(istek, withObserver: g)
    analizci.analyze()
    if let e = g.hata { throw Hata("ses analizi: \(e)") }
    try jsonYaz(["kaynak": girdi.path, "pencereler": g.pencereler], cikti)
    print("\(g.pencereler.count) pencere → \(cikti)")
}

// MARK: - ortak resim yardımcıları

func resimYukle(_ u: URL) throws -> CIImage {
    guard let kaynak = CGImageSourceCreateWithURL(u as CFURL, nil),
          let cg = CGImageSourceCreateImageAtIndex(kaynak, 0, nil) else { throw Hata("resim açılamadı: \(u.path)") }
    let oz = CGImageSourceCopyPropertiesAtIndex(kaynak, 0, nil) as? [CFString: Any]
    let yon = (oz?[kCGImagePropertyOrientation] as? UInt32).flatMap { CGImagePropertyOrientation(rawValue: $0) } ?? .up
    let ci = CIImage(cgImage: cg).oriented(yon)                     // EXIF yönünü uygula: dik görüntü
    return ci.transformed(by: CGAffineTransform(translationX: -ci.extent.origin.x, y: -ci.extent.origin.y))
}

func resimYaz(_ ci: CIImage, _ u: URL, _ ctx: CIContext) throws {
    let srgb = CGColorSpace(name: CGColorSpace.sRGB)!
    switch u.pathExtension.lowercased() {
    case "jpg", "jpeg":
        try ctx.writeJPEGRepresentation(of: ci, to: u, colorSpace: srgb,
                                        options: [kCGImageDestinationLossyCompressionQuality as CIImageRepresentationOption: 0.92])
    default:
        try ctx.writePNGRepresentation(of: ci, to: u, format: .RGBA8, colorSpace: srgb)
    }
}

// MARK: - arkaplan-sil

func arkaplanSil(_ a: Arg) async throws {
    let girdi = URL(fileURLWithPath: try a.pos(0)), cikti = URL(fileURLWithPath: try a.pos(1))
    let ctx = CIContext()
    let dik = try resimYukle(girdi)
    guard let cg = ctx.createCGImage(dik, from: dik.extent) else { throw Hata("resim hazırlanamadı") }
    let el = ImageRequestHandler(cg)
    guard let gozlem = try await el.perform(GenerateForegroundInstanceMaskRequest()) else {
        throw Hata("ön planda bir nesne/kişi bulunamadı")
    }
    let kirp = (a.secenek["--kirp"] ?? "hayir") == "evet"
    let maskeli = try gozlem.generateMaskedImage(for: gozlem.allInstances, imageFrom: el, croppedToInstancesExtent: kirp)
    try resimYaz(CIImage(cvPixelBuffer: maskeli), cikti, ctx)
    if let m = a.secenek["--maske"] {
        let maske = try gozlem.generateScaledMask(for: gozlem.allInstances, scaledToImageFrom: el)
        try resimYaz(CIImage(cvPixelBuffer: maske), URL(fileURLWithPath: m), ctx)
    }
    let rapor: [String: Any] = ["ornek_sayisi": gozlem.allInstances.count, "boyut": "\(cg.width)x\(cg.height)", "cikti": cikti.path]
    print(String(data: try JSONSerialization.data(withJSONObject: rapor, options: [.sortedKeys]), encoding: .utf8)!)
}

// MARK: - yetenek

func yetenek() throws {
    let d: [String: Any] = [
        "kare_hizi_donusumu": VTFrameRateConversionConfiguration.isSupported,
        "hareket_bulanikligi": VTMotionBlurConfiguration.isSupported,
        "zamansal_gurultu": VTTemporalNoiseFilterConfiguration.isSupported,
        "super_cozunurluk": VTSuperResolutionScalerConfiguration.isSupported,
        "optik_akis": VTOpticalFlowConfiguration.isSupported,
    ]
    let veri = try JSONSerialization.data(withJSONObject: d, options: [.sortedKeys])
    print(String(data: veri, encoding: .utf8)!)
}

@main
struct MedyaApple {
    static func main() async {
        let a = CommandLine.arguments
        guard a.count >= 2 else {
            fputs("kullanım: medya-apple yavaslat|analiz|ses-olay|arkaplan-sil|yetenek …\n", stderr); exit(2)
        }
        let arg = Arg(Array(a.dropFirst(2)))
        do {
            switch a[1] {
            case "yavaslat": try await yavaslat(arg)
            case "analiz": try await analiz(arg)
            case "ses-olay": try sesOlay(arg)
            case "arkaplan-sil": try await arkaplanSil(arg)
            case "yetenek": try yetenek()
            default: fputs("bilinmeyen komut: \(a[1])\n", stderr); exit(2)
            }
        } catch {
            fputs("HATA: \(error)\n", stderr); exit(1)
        }
    }
}
