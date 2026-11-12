import Foundation
import Vision
import CoreImage
import AppKit

// Isolates the photo's subject from its background and reports the face box.
// Writes an RGBA PNG (background fully transparent) plus a JSON sidecar.

let args = CommandLine.arguments
guard args.count >= 3 else {
    FileHandle.standardError.write("usage: Segment <input> <output.png>\n".data(using: .utf8)!)
    exit(2)
}
let inURL = URL(fileURLWithPath: args[1])
let outURL = URL(fileURLWithPath: args[2])

guard let src = CIImage(contentsOf: inURL) else {
    FileHandle.standardError.write("could not read image\n".data(using: .utf8)!)
    exit(1)
}
let w = src.extent.width
let h = src.extent.height

let handler = VNImageRequestHandler(ciImage: src, options: [:])

// Face rectangle, reported in normalised bottom-left-origin coordinates.
var faceJSON = "null"
let faceReq = VNDetectFaceRectanglesRequest()
do {
    try handler.perform([faceReq])
    if let f = (faceReq.results ?? []).max(by: { $0.boundingBox.width < $1.boundingBox.width }) {
        let b = f.boundingBox
        faceJSON = """
        {"x":\(b.origin.x),"y":\(b.origin.y),"w":\(b.size.width),"h":\(b.size.height)}
        """
    }
} catch {
    FileHandle.standardError.write("face detect failed: \(error)\n".data(using: .utf8)!)
}

// Foreground instance mask, then composite the subject over transparency.
let maskReq = VNGenerateForegroundInstanceMaskRequest()
do {
    try handler.perform([maskReq])
} catch {
    FileHandle.standardError.write("mask request failed: \(error)\n".data(using: .utf8)!)
    exit(1)
}
guard let obs = maskReq.results?.first, !obs.allInstances.isEmpty else {
    FileHandle.standardError.write("no foreground instance found\n".data(using: .utf8)!)
    exit(1)
}

let maskBuffer = try obs.generateScaledMaskForImage(forInstances: obs.allInstances, from: handler)
let mask = CIImage(cvPixelBuffer: maskBuffer)

// Scale the mask to the source extent in case Vision returned a smaller buffer.
let sx = w / mask.extent.width
let sy = h / mask.extent.height
let scaledMask = mask.transformed(by: CGAffineTransform(scaleX: sx, y: sy))

let clear = CIImage(color: .clear).cropped(to: src.extent)
guard let blend = CIFilter(name: "CIBlendWithMask") else { exit(1) }
blend.setValue(src, forKey: kCIInputImageKey)
blend.setValue(clear, forKey: kCIInputBackgroundImageKey)
blend.setValue(scaledMask, forKey: kCIInputMaskImageKey)
guard let composited = blend.outputImage else { exit(1) }

let ctx = CIContext()
guard let cs = CGColorSpace(name: CGColorSpace.sRGB) else { exit(1) }
try ctx.writePNGRepresentation(of: composited,
                               to: outURL,
                               format: .RGBA8,
                               colorSpace: cs)

let meta = """
{"width":\(Int(w)),"height":\(Int(h)),"face":\(faceJSON),"instances":\(obs.allInstances.count)}
"""
try meta.write(to: outURL.appendingPathExtension("json"), atomically: true, encoding: .utf8)
print(meta)
