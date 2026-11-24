import PDFKit
import AppKit
let a = CommandLine.arguments
let doc = PDFDocument(url: URL(fileURLWithPath: a[1]))!
if a.count == 2 { print(doc.pageCount); exit(0) }
let p = doc.page(at: Int(a[2])! - 1)!
let img = p.thumbnail(of: NSSize(width: 1000, height: 1414), for: .mediaBox)
let rep = NSBitmapImageRep(data: img.tiffRepresentation!)!
try! rep.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: a[3]))
