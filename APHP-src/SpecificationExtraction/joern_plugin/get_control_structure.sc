import org.json4s.DefaultFormats
import org.json4s.native.Serialization.{read => jsonRead}
import org.json4s.native.Serialization.{write, writePretty}

@main def exec(cpgFile: String, outFile: String) = {
    importCpg(cpgFile)
    implicit val formats: DefaultFormats.type = DefaultFormats

    val statements = cpg.controlStructure.controlStructureType("IF")
    var output = ""
    for (statment <- statements){
        val lineNumber = statment.lineNumber
        val condition = statment.condition.code.l
        val lineNumbersWhenTrue = statment.whenTrue.ast.lineNumber.l
        
        val elementMap = Map(
            "lineNumber" -> lineNumber,
            "condition" -> condition,
            "lineNumbersWhenTrue" -> lineNumbersWhenTrue
        )
        val json = write(elementMap)

        // append output
        output += json + "\n"
    }
    
    println(output)
    output |> outFile

}

// cpg.controlStructure.controlStructureType("IF").whenTrue.ast.lineNumber.l 