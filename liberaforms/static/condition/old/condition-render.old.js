

var _conditions={}
var _fields={}


class Field {
    constructor(name, group) {
        this.$group = group
        this.$group.find("label:first").append("<span class='stats'></span>")
        this.name = name
        this.conditioners = []
        this.conditioneds = []
    }
    showConditioneds(condition) {
        console.log('show conditioneds')
        this.conditioneds = condition.conditioned
        var self=this
        this.conditioneds.forEach(function(conditioned) {
            _fields[conditioned].addConditioner(self.name)
            _fields[conditioned]._show()
        });
        console.log(_fields)
        this.$group.find(".stats").html(" Rs - "+this.conditioners.length+" Ds - "+this.conditioneds.length)
    }
    hideConditioneds() {
        console.log('hide conditioneds')
        //console.log(this.conditioneds)
        var self=this
        this.conditioneds.forEach(function(conditioned) {
            _fields[conditioned].removeConditioner(self.name)
            _fields[conditioned]._hide()
            if (_fields[conditioned].conditioners.length == 0){
                _fields[conditioned].hideConditioneds()
            }
        });
        this.conditioneds = []
        console.log(_fields)
        this.$group.find(".stats").html(" Rs - "+this.conditioners.length+" Ds - "+this.conditioneds.length)
    }
    addConditioner(conditioner) {
        if (this.conditioners.includes(conditioner) == false) {
            this.conditioners.push(conditioner)
        }
        console.log("conditioners after add: "+this.conditioners)
        var self=this
        this.conditioneds.forEach(function(conditioned) {
            /*
            _fields[conditioned].removeConditioner(self.name)
            _fields[conditioned]._show()
            if (_fields[conditioned].conditioners.length == 0){
                _fields[conditioned].hideConditioneds()
            }*/
        });
        this.$group.find(".stats").html(" Rs - "+this.conditioners.length+" Ds - "+this.conditioneds.length)
    }
    removeConditioner(conditioner) {
        this.conditioners = this.conditioners.filter(function(item) {
            return item !== conditioner
        });
        console.log("conditioners after remove: "+this.conditioners)
        this.$group.find(".stats").html(" Rs - "+this.conditioners.length+" Ds - "+this.conditioneds.length)
    }
    _show() {
        if (this.conditioners.length > 0) {
            this.$group.slideDown("fast")
            if (this.conditioneds.length == 0){
                if (_conditions[this.name] != undefined) {
                    //console.log('retrived value: ' + this.getSelectedValues(_conditions[this.name]))
                }
            }
        }
    }
    _hide() {
        if (this.conditioners.length == 0) {
            this.$group.hide()
        }
    }
    getSelectedValues(condition) {
        console.log("get values for: "+this.name+" Type: "+condition.field_type)
        //var condition = _conditions[this.name]
        var field_name = this.name
        var values = []
        if (condition.field_type == "select") {
            console.log(this.$group.find('select[name="'+field_name+'"]'))
            values.push(this.$group.find('select[name="'+field_name+'"]').val())
            console.log(values)
            return values
        }
        if (condition.field_type == "checkbox") {
            field_name=field_name+"[]"
        }
        this.$group.find('input[name="'+field_name+'"]').each(function() {
            if ($(this).prop('checked') == true) {
                values.push($(this).val())
            }
        });
        console.log("getSelectedValues result:")
        console.log(values)
        return values
    }
    doesMatch(condition) {
        var values = this.getSelectedValues(condition)
        console.log("does match")
        console.log(values)
        console.log(condition.values)
        console.log(condition)
        if (condition.operator == "equals"){
            if (JSON.stringify(values) === JSON.stringify(condition.values)){
                return true
            }
            return false
        }
        if (condition.operator == "includes" && condition.and_or == "and"){
            condition.values.forEach(function(condition_value) {
                if (values.includes(condition_value) == false) {
                    return false
                }
            });
            return true
        }
        if (condition.operator == "includes" && condition.and_or == "or") {
            values.forEach(function(value) {
                if (condition.values.includes(value)) {
                    return true
                }
            });
            return false
        }
        return false
    }
}



function initiateConditions(saved_conditions) {
    _conditions={}
    _fields={}
    console.log("initiate")
    $("#gngform").find(".form-group").each(function() {
        name = $(this).find("label:first").prop("for")
       _fields[name] = new Field(name, $(this))
    });

    saved_conditions.forEach(function(condition) {
        var conditioner=condition.conditioners[0]
        
        if (_conditions[conditioner.name] == undefined) {
            _conditions[conditioner.name] = {}
            _conditions[conditioner.name]['conditions'] = []
            _conditions[conditioner.name]['field_type']=conditioner["type"]
        }
        
        var data={}
        data["id"]=conditioner.idx
        data["field_type"]=conditioner.type
        data["operator"]=conditioner.operator
        data["and_or"]=conditioner.and_or
        data["high"]=conditioner.high
        data["low"]=conditioner.low
        data["values"]=[]
        conditioner["values"].forEach(function(value){
            data["values"].push(value.value)
        })
        data["conditioned"]=condition["conditioned"]
        _conditions[conditioner.name]['conditions'].push(data)
        
        condition.conditioned.forEach(function(name) {
            $("#gngform").find("label[for="+name+"]").closest(".form-group").hide()
        });
    });
    console.log(_conditions)
    
    Object.keys(_conditions).forEach(function(key) {
        
        var field_name=key
        if (_conditions[key].field_type == "checkbox") {
            var field_name=field_name+"[]"
        }
            
        event = $('#gngform').on('change', '[name="'+field_name+'"]', function() {
            console.log("does match!: " + _fields[key])
            console.log("does match!: " + _fields[key].doesMatch(_conditions[key]))
        });
        /*
                
                console.log("does match!: " + _fields[key])
                console.log("does match!: " + _fields[key].doesMatch(_conditions[key]))
                
                console.log("checkbox group clicked")
                console.log("checkbox clicked: "+$(this).prop("value"))

                var group = $(this).closest(".form-group")
                values = _fields[key].getSelectedValues(_conditions[key])
                console.log("checkbox checked values")
                console.log(values)
                
                _conditions[key].conditions.forEach(function(condition) {
                
                
                
                    if (condition.operator == "equals"){
                        
                        if (JSON.stringify(values) === JSON.stringify(condition.values)){
                            _fields[key].showConditioneds(condition)
                        } else {
                            //_fields[key].hideConditioneds(condition.conditioned)
                            _fields[key].hideConditioneds()
                        }
                    }
                });
                //console.log("checking includes")
                //var conditioned_to_hide = []
                _conditions[key].conditions.forEach(function(condition) {
                    if (condition.operator == "includes"){
                        //console.log("checking includes: "+condition.and_or)
                        if (condition.and_or == "and") {
                            var match = true
                            condition.values.forEach(function(condition_value) {
                                if (values.includes(condition_value) == false) {
                                    match = false
                                }
                            });
                            if (match == true) {
                                _fields[key].showConditioneds(condition)
                                
                            }
                        }
                        if (condition.and_or == "or") {
                            var matched = false
                            values.forEach(function(value) {
                                if (condition.values.includes(value)) {
                                    //must_show = must_show.concat(condition.conditioned)
                                    //showFields(condition.conditioned)
                                    //console.log("concat must show")
                                    //console.log(must_show)
                                    if (matched == false) {
                                        _fields[key].showConditioneds(condition)
                                        matched = true
                                    }
                                }
                            });
                        }
                        if (matched == false) {
                            //_fields[key].hideConditioneds(condition.conditioned)
                            _fields[key].hideConditioneds()
                        }
                    }

                });
            });        
        }
        if (_conditions[key].field_type == "select" || _conditions[key].field_type == "radio") {
            var field_name=key
            
            event = $('#gngform').on('change', '[name="'+field_name+'"]', function() {
                
                //var group = $(this).closest(".form-group")
                //value = _fields[key].getSelectedValues(_conditions[key])[0]
                //var value = $(this).val()
                _conditions[key].conditions.forEach(function(condition) {
                    //if (value == condition.values[0]){
                    if (_fields[key].doesMatch(condition)) {
                        //console.log("match!")
                        //_fields[key].addConditioneds(condition.conditioned)
                        _fields[key].showConditioneds(condition)
                    } else {
                        //_fields[key].hideConditioneds(condition.conditioned)
                        _fields[key].hideConditioneds()
                    }
                    
                });
                
            });
        }
        */
    });
    //rendered_conditions.push({"name": condition.name, "event": event})

}

function getSelectCondition(group) {
    var select = group.find("select")
                var value = $(select).val()
                _conditions[key].conditions.forEach(function(condition) {
                    if (value == condition.values[0]){
                        //console.log("match!")
                        //_fields[key].addConditioneds(condition.conditioned)
                        return condition.conditioned
                        _fields[key].showConditioneds(condition)
                    } else {
                        //_fields[key].hideConditioneds(condition.conditioned)
                        _fields[key].hideConditioneds()
                    }
                    
                });
    
}

function stopTest() {
    var _conditions={}
    var _fields={}
    $("#gngform").find("._possible_conditioned").show()
    
}
