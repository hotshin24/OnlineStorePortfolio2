import PDFKit
import Foundation
let a = CommandLine.arguments
let front = PDFDocument(url: URL(fileURLWithPath: a[1]))!
let orig = PDFDocument(url: URL(fileURLWithPath: a[2]))!
for i in (0..<front.pageCount).reversed() { orig.insert(front.page(at: i)!, at: 0) }
print(orig.write(to: URL(fileURLWithPath: a[3])), orig.pageCount)
