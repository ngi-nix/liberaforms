
// https://javascript.info/class-inheritance

class GNGform {
    constructor() {
        this.form = $("#gngform")
        this.conditioner_icon='<i class="conditioner_icon fa fa-star" aria-hidden="true"></i>'
        this.plus_icon='<i class="conditioned_icon fa fa-plus-square" aria-hidden="true"></i>'
        this.minus_icon='<i class="conditioned_icon fa fa-minus-square" aria-hidden="true"></i>'
    }
    addPossibleConditionerControls() {
        var self=this
        this.form.find(".form-group[_possible_conditioner=true]").each(function() {
            self._addControlsToGroup(this, self.conditioner_icon)
        });
    }
    addConditionedControls() {
        var possible_conditioned = this.form.find("._possible_conditioned")
        console.log(possible_conditioned)
        for (var i = 0; i < possible_conditioned.length; i++) {
            if ( $(possible_conditioned[i]).find('._active_conditioner').length ) {
                continue
            }
            if ( $(possible_conditioned[i]).find("label:first").hasClass('activeConditionedGroup')){
                this._addControlsToGroup($(possible_conditioned[i]), this.minus_icon)
            } else {
                this._addControlsToGroup($(possible_conditioned[i]), this.plus_icon)
            }
        }
    }
    _addControlsToGroup(group, icon) {
        if ( $(group).find("span.label-description").length ) {
            var label=$(group).find("span.label-description")
            $(icon).insertBefore(label);
        }else{
            var label=$(group).children('label').first()
            $(icon).insertAfter(label);
        }
    }
    removeControls() {
        this.form.find(".conditioner_icon").remove()
        this.form.find(".conditioned_icon").remove()
    }
    rebase() {
        this.removeControls()
        this.form.find("._active_conditioned").removeClass("_active_conditioned")
        this.form.find("._active_conditioner").removeClass("_active_conditioner")
        this.form.find(".activeConditionerGroup").removeClass("activeConditionerGroup")
        this.form.find(".activeConditionedGroup").removeClass("activeConditionedGroup")
    }
    findGroup(name) {
        return this.form.find("label[for='"+name+"']").closest('.form-group')
    }
}

let form = new GNGform()

class Condition {
    constructor(idx, display) {
        this.idx=Number(idx)
        this.label=""
        this.name=""
        this.operator="equals"
        this.and_or="and"
        this.high=null
        this.low=null
        this.values=[]
        this.tmp_values=[]
        this.conditioner_group=null
        this.conditioner_type=null
        this.conditioned_groups=[]
        this.display=new Display(this, display)
        form.rebase()
    }
    addConditionerGroup(group) {
        this.conditioner_group = new ConditionerGroup(group)
        this.conditioner_group.activate()
        this.label = this.conditioner_group.label
        this.name = this.conditioner_group.name
        this.conditioner_type = this.conditioner_group.getType()
        this.tmp_values = this.conditioner_group.getValues()
        this.display.update()
        this.display.addHighLights()
        form.removeControls()
        form.addConditionedControls()
    }
    updateConditionerValues() {
        this.tmp_values = this.conditioner_group.getValues()
        this.display.update()
        this.display.addHighLights()
    }
    addConditionedGroup(group) {
        var group = new ConditionedGroup(group)
        this.conditioned_groups.push(group)
        group.activate()
        this.display.update()
        this.display.addHighLights()
    }
    removeConditionedGroup(group) {
        var tmp_group = new ConditionedGroup(group)
        var new_conditioned_groups=[]
        for (var i = 0; i < this.conditioned_groups.length; i++) {
            if (this.conditioned_groups[i]["name"] != tmp_group.name) {
                new_conditioned_groups.push(this.conditioned_groups[i])
            }
        }
        this.conditioned_groups = new_conditioned_groups
        this.display.update()
        this.display.addHighLights()
        group.find(".activeConditionedGroup").removeClass("activeConditionedGroup")
    }
    activate() {
        if (this.conditioner_group) {
            this.conditioner_group.setValues(this.values)
            this.conditioner_group.activate()
        }
        this.display.addHighLights()
        for (var i = 0; i < this.conditioned_groups.length; i++) {
            this.conditioned_groups[i].group.find("label:first").addClass("activeConditionedGroup")
        }
    }
    edit() {
        form.rebase()
        this.activate()
        for (var i = 0; i < this.conditioned_groups.length; i++) {
            this.conditioned_groups[i].group.find("label:first").addClass("activeConditionedGroup")
        }
        form.addConditionedControls()
        this.display.edit()
    }
    cancelEdition() {
        this.tmp_values = this.values
        this.display.cancelEdition()
        this.conditioner_group.setValues(this.values)
        form.rebase()
    }
    save() {
        this.values = this.tmp_values
        this.display.save()
        form.rebase()
    }
    getDisplayElement() {
        return this.display.display
    }
    toggleOperator() {
        if (this.operator == "equals") {
            this.operator = "includes"
        } else {
            this.operator = "equals"
            this.and_or = "and"
        }
        this.display.update()
    }
    toggleAnd_Or() {
        if (this.and_or == "and") {
            this.and_or = "or"
        } else {
            this.and_or = "and"
        }
        this.display.update()     
    }
    removeDisplay() {
        this.display.display.remove()
        form.rebase()
    }
    getConditionedLabels() {
        var labels=$("<div />")
        this.conditioned_groups.forEach(function(group) {
            labels.append($("<span />").append(group.label))
        });
        return labels
    }
    load(saved_condition) {
        var conditioner = saved_condition.conditioners[0]
        this.name = conditioner.name
        this.operator = conditioner.operator
        this.and_or = conditioner.and_or
        this.low = conditioner.low
        this.high = conditioner.high
        this.values = conditioner.values
        var form_group = form.findGroup(conditioner.name)
        this.conditioner_group = new ConditionerGroup(form_group)
        
        this.conditioner_type = conditioner.type
        
        this.label = this.conditioner_group.label
        this.conditioner_group.setValues(this.values)
        this.tmp_values = this.conditioner_group.getValues()
        
        var self=this
        saved_condition.conditioned.forEach(function(conditioned_name) {
            var form_group = form.findGroup(conditioned_name)
            var conditioned_group = new ConditionedGroup(form_group)
            self.conditioned_groups.push(conditioned_group)
        })      
        this.display.update()
    }
}

class Display {
    constructor(condition, display) {
        this.condition=condition
        this.display=display
        this.display.removeClass("condition_template")
        this.display.attr('idx', this.condition.idx)
        this.display.appendTo("#conditions")
        this.empty_conditioned_text="Select a form field <i class='conditioned_icon fa fa-plus-square' aria-hidden='true'></i>"
        this.update()
    }
    activate() {
        this.display.find("thead").addClass("activeConditionGroup")
    }
    isActive() {
        if (this.display.find("thead").hasClass("activeConditionGroup")) {
            return true
        }
        return false
    }
    edit() {
        this.activate()
        this.updateControls()
        this.addHighLights()
    }
    cancelEdition() {
        this.display.find(".activeConditionGroup").removeClass("activeConditionGroup")
        this. removeHighlights()
        this.update()
        this.updateControls()
    }
    save() {
        this.display.find(".activeConditionGroup").removeClass("activeConditionGroup")
        this. removeHighlights()
        this.updateControls()
    }
    update(){
        // reload values
        if (this.condition.label) {
            this.display.find(".conditioner_label").html("<span>"+this.condition.label+"</span>")

            var labels=$("<div />")
            var self=this
            this.condition.tmp_values.forEach(function(value) {
                console.log(value)
                labels.append($("<span />").append(value['label']))
                console.log(self.conditioner_type)
                if (self.condition.conditioner_type == "checkbox") {
                    labels.append("<span class='and_or'></span>")
                }
            });
            labels.find(".and_or:last").remove()
            this.display.find(".conditioner_value").html(labels);
        }
        if (this.condition.conditioned_groups.length > 0) {
            this.display.find(".conditioned_groups_labels").html(this.condition.getConditionedLabels())
        } else if (this.display.find(".conditioner_value").html()) {
            this.display.find(".conditioned_groups_labels").html(this.empty_conditioned_text)
        }
        this.updateControls()
        this.display.show()
    }

    updateControls() {
        if (this.display.find(".activeConditionGroup").length) {
            this.display.find(".edit_condition").hide()
            if (this.condition.conditioned_groups.length > 0 && this.condition.tmp_values.length > 0) {
                this.display.find(".save_condition").show()
                if (this.condition.values.length > 0) {
                    this.display.find(".cancel_edition").show()
                }
            } else {
                this.display.find(".save_condition").hide()
            }
        } else {
            this.display.find(".save_condition").hide()
            this.display.find(".cancel_edition").hide()
            if (this.condition.conditioned_groups.length > 0 && this.condition.tmp_values.length > 0) {
                this.display.find(".edit_condition").show()
            }
        }
        this.updateOperator()
        this.display.find(".delete_condition").prop('disabled', false)
    }
    updateOperator(){
        if (this.condition.conditioner_type != "checkbox") {
            return
        }
        console.log("update operator")
        console.log("and_or: "+this.condition.and_or)
        //console.log(this.condition.operator)
        this.display.find(".and_or").html(this.condition.and_or)
        this.display.find(".operator").hide()
        
        if (this.isActive()) {
            var toggler = this.display.find(".toggle_equals_operator")
            if (this.condition.operator == "equals") {
                toggler.find(".equals_true").addClass("btn-primary")
                toggler.find(".equals_true").removeClass("btn-default")
                toggler.find(".equals_false").removeClass("btn-primary")
                toggler.find(".equals_false").addClass("btn-default")
            } else { 
                toggler.find(".equals_true").addClass("btn-default")
                toggler.find(".equals_true").removeClass("btn-primary")
                toggler.find(".equals_false").removeClass("btn-default")
                toggler.find(".equals_false").addClass("btn-primary")
            }
            toggler.show()
            if (this.condition.operator == "includes") {
                this.display.find(".and_or").addClass("active_and_or")
            }
        } else {
            if (this.condition.operator == "equals") {
                this.display.find(".equals_operator").show()
            } else {
                this.display.find(".includes_operator").show()
            }
            this.display.find(".and_or").removeClass("active_and_or")
        }
    }
    addHighLights() {
        this.display.find("thead").addClass("activeConditionGroup")
        if (this.condition.label != "") {
            this.display.find(".conditioner_label").find("span").addClass("activeConditionerGroup")
        }
        if (this.condition.tmp_values.length > 0) {
            this.display.find(".conditioner_value").find("span").addClass("activeConditionerGroup")
        }
        if (this.condition.conditioned_groups.length > 0) {
            this.display.find(".conditioned_groups_labels").find("span").addClass("activeConditionedGroup")
        }
    }
    removeHighlights() {
        this.display.find(".activeConditionGroup").removeClass("activeConditionGroup")
        this.display.find(".activeConditionerGroup").removeClass("activeConditionerGroup")
        this.display.find(".activeConditionedGroup").removeClass("activeConditionedGroup")
    }
}


class Group {
    constructor(group) {
        var label = group.find('label:first').clone()
        label.find('i').remove().find('span').remove() // remove stuff we have appended
        this.name = label.prop("for")
        this.label = label.html()
        this.group = group
    }
}

class ConditionerGroup extends Group {
    static find(name) {
        group = $("#gngform").find("label[for="+name+"]").closest(".form-group")
        if (group == undefined) {
            return null;
        }
        return new ConditionerGroup(group);
    }
    constructor(group) {
        super(group)
    }
    activate() {     
        this.group.find("[name='"+this.name+"']").addClass("_active_conditioner") // inputs, selects, radios, ..
        this.group.find("[name='"+this.name+"[]']").addClass("_active_conditioner") // checkbox groups []
        this.group.find("label:first").addClass("activeConditionerGroup")
    }
    getType(){
        if (this.group.find("select").length) {
            return "select"
        }
        return this.group.find("input:first").prop('type')
    }
    getValues(){
        var values = []
        if (this.group.find('.checkbox-group').length || this.group.find('.radio-group').length){
            console.log("get group value")
            this.group.find("INPUT").each(function() {
                if($(this).prop('checked') == true){
                    var label=$(this).siblings("label[for='"+$(this).prop('id')+"']").html()
                    values.push({'label': label, 'value': $(this).val()})
                }
            });
            return values
        }
        var element=this.group.find('.form-control')
        if (element != undefined){
            var element_nodeName = $(element).prop('nodeName')
            console.log( "nodeName: " + element_nodeName )
            if (element_nodeName == "SELECT"){
                var value = $(element).val()
                var label = $(element).find("[value="+value+"]").html()
                return [{'label': label, 'value': value}]
            }
        }
        return values
    }
    setValues(values) {
        console.log("set conditioner values")
        //console.log(values)
        if (this.group.find('.checkbox-group').length || this.group.find('.radio-group').length){
            this.group.find("INPUT").prop('checked', false)
            for (let dict of Object.values(values)) {
              this.group.find("INPUT[value="+dict.value+"]").prop('checked', true)
            }
            return
        }
        var element=this.group.find('.form-control')
        if (element != undefined){
            var element_nodeName = $(element).prop('nodeName')
            //console.log( "nodeName: " + element_nodeName )
            if (element_nodeName == "SELECT"){
                $(element).val(values[0]['value'])
            }
        }
    }
}

class ConditionedGroup extends Group {
    constructor(group) {
        super(group)
    }
    activate() {
        this.group.find("label:first").addClass("activeConditionedGroup")
    }
}
