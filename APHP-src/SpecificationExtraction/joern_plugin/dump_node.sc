@main def exec(cpgFile: String, outFile: String) = {
   importCpg(cpgFile)
   cpg.all.toJson |> outFile
}

// run example
// joern --script dump_nodes.sc --params cpgFile=/root/bug-tools/demo/joern/after.bin,outFile=/tmp/output.log