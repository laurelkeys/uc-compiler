Program: 
    FuncDef: 
        Type: ['int']   @ 1:1
        Decl: ID(name='main'  )
            FuncDecl: 
                VarDecl: 
                    Type: ['int']   @ 1:1
        Compound:    @ 1:1
            Decl: ID(name='n'  )
                VarDecl: 
                    Type: ['int']   @ 2:5
            Decl: ID(name='reverse'  )
                VarDecl: 
                    Type: ['int']   @ 2:5
                Constant: int, 0   @ 2:22
            Decl: ID(name='rem'  )
                VarDecl: 
                    Type: ['int']   @ 2:5
            Print:    @ 3:5
                Constant: string, "Enter a number: "   @ 3:11
            Read:    @ 4:5
                ID: n   @ 4:10
            While:    @ 5:5
                BinaryOp: !=   @ 5:12
                    ID: n   @ 5:12
                    Constant: int, 0   @ 5:17
                Compound:    @ 5:1
                    Assignment: =   @ 6:9
                        ID: rem   @ 6:9
                        BinaryOp: %   @ 6:15
                            ID: n   @ 6:15
                            Constant: int, 10   @ 6:19
                    Assignment: =   @ 7:9
                        ID: reverse   @ 7:9
                        BinaryOp: +   @ 7:19
                            BinaryOp: *   @ 7:19
                                ID: reverse   @ 7:19
                                Constant: int, 10   @ 7:29
                            ID: rem   @ 7:34
                    Assignment: /=   @ 8:9
                        ID: n   @ 8:9
                        Constant: int, 10   @ 8:14
            Print:    @ 10:5
                ExprList:    @ 10:11
                    Constant: string, "Reversed Number: "   @ 10:11
                    ID: reverse   @ 10:32
            Return:    @ 11:5
                Constant: int, 0   @ 11:12
