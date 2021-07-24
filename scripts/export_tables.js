state = Calc.getState()

for (let i = 0; i < state.expressions.list.length; i++) {
    if (state.expressions.list[i].type == "folder") {
        console.log("#" + state.expressions.list[i].title)
    }
    if (state.expressions.list[i].type == "table") {
        for (let j = 0; j < state.expressions.list[i].columns.length; j++) {
            console.log(state.expressions.list[i].columns[j].latex + " = " + state.expressions.list[i].columns[j].values.toString())
        }
    }
}