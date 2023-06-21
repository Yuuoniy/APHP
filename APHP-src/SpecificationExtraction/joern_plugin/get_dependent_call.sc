import io.shiftleft.semanticcpg.language._
import io.shiftleft.codepropertygraph.Cpg


private def getRetvalDep(name: String,idx:Long): List[String] = {
    var retval:String = ""
    var retval_dep:List[String] = cpg.call.filter(_.name.contains("<")==false).filter(call=>{
        if (call.id < idx && call.inAssignment.target.l.size!=0) {
            retval = call.inAssignment.target.l.head.l.code.l.head
            retval == name
        }else{
            false
        }
    }).name.l
    retval_dep
}

private def getArgDep(name: String,idx:Long): List[String] = {
    var arg_dep:List[String]  = cpg.call.filter(_.name.contains("<")==false).filter(call=>{
        if(call.id>idx){
            // print("[0] call.id>idx: "+call.name+'\n')
            false
        }else if(call.argument.size==0){
            // print("[1] all.argument.size==0: "+call.name+'\n')
            false
        }else{
            // print("[2]: "+call.name+'\n')
            (call.argument(1).code == name) ||  (call.argument.size>1 && call.argument(2).code == name)
        }
        }).name.l

    arg_dep
}



@main def main(cpgFile:String,func:String,code:String,outFile:String): List[String] = {
    // run.ossdataflow
    // use call code to identify the call
    // println(func)
    loadCpg(cpgFile)
    var arg1:String = cpg.call.name(func).filter(_.code == code).argument(1).code.head 
    var alias:String = ""
    // print(arg1)
    // only get backward function call
    // get func call index 
    var idx:Long = cpg.call.name(func).filter(_.code == code).id.l.reduceLeft(_ max _) 
    // var idx:Long = cpg.call.name(func).filter(_.code == code).id.l.head 

    // find alias of arg1, like arg1 = val, then get the val.

    var assignments =  cpg.assignment.filter(_.argument(1).code==arg1).argument(2).l.filter(i=>{i.code.contains("NULL")==false})
    if(assignments.size == 0){
        println("No aliases found for " + arg1)
    }
    else{
        // println("Found alias" + assignments.head.code)
        alias = assignments.head.code
    }
    
    // get functions having argument depends on func
    var arg_dep :List[String] = getArgDep(arg1,idx)
    
    if (alias!=""){
        var alias_arg_dep:List[String] = getArgDep(alias,idx)
        arg_dep = arg_dep:::alias_arg_dep
    }

    var retval:String = ""
  
    // get functions having return value depends on func
    var retval_dep:List[String] = getRetvalDep(arg1,idx)
    
    

    // combine function list
    var all_dep :List[String] = arg_dep:::retval_dep
    all_dep = all_dep.toSet.toList.filter(i => {i != func})


    if (all_dep.size == 0){
        // field sensitive, if we can't find the dependent on the field, then we find it one the struct.
        if (arg1.contains("->")){
            var struct_name = arg1.split("->").head
            if (struct_name.head=='&'){
                struct_name = struct_name.tail
            }
            
            arg_dep = getArgDep(struct_name,idx)
            retval_dep = getRetvalDep(struct_name,idx)

            all_dep =arg_dep:::retval_dep
            all_dep = all_dep.toSet.toList.filter(i => {i != func})
        }
        
    }else{
        println("[Found data dependency]: " + "arg_dep: " + arg_dep.mkString(",") + "," + "retval_dep: "+ retval_dep.mkString(","))
    }


    all_dep |> outFile
    return all_dep
}


// joern --script get_call.sc --params cpgFile=/root/bug-tools/demo/joern/after.bin,func=usb_put_hcd,code="usb_put_hcd(hcd)",outFile=/tmp/output.log

