var graph;
var helper_expression = {};
var GRAPH_MODIFIED = false; //Whether or not the graph has been modified when editing a template.
$(document).ready(function(){
    var graph_initialized = false;
    // Open the Graph-drawer
	$('#opt_graph').change(function(){
		if($(this).is(':checked')){
			$('#graph_modal').modal('show').one('shown.bs.modal', function(){
                var graph_expressions =  $('#get_graph').text();
                if (!graph_initialized && !MODIFY) {
                    dcg_init_graph();
                    graph_initialized = true;
                } else if (!graph_initialized && MODIFY && (graph_expressions != "[]") && (graph_expressions != "None") && (graph_expressions != "")){
                    dcg_edit_graph();
                    graph_initialized = true;
                } else if (!graph_initialized && MODIFY && ((graph_expressions == "[]") || (graph_expressions == "None") || (graph_expressions == ""))){
                    dcg_init_graph();
                    graph_initialized = true;
                } else {
                    dcg_refresh_variables();
                }
			});
		}
	});
});

/**
 * Initialize the graph with given options and preferences.
 */
function dcg_init_graph(){
	$('#graph_container').html("");
	var elt = document.getElementById('graph_container');
	graph = Desmos.Calculator(elt, { //Set options for the DCG
		keypad: false,
        expressionsTopbar: false
	});
	graph.setExpression({id: 'graph1', latex: 'f(x)='});
    dcg_refresh_variables();
    refresh_char_colors('.dcg-template-mathquill');
    $('.dcg-template-mathquill').addClass('input_mathquill');
    GRAPH_MODIFIED = true;
}

/**
 * Initialize the graph with given options and preferences in the game.
 */
function dcg_init_game_graph(){
    var elt = document.getElementById('graph_container');
	graph = Desmos.Calculator(elt, { //Set options for the DCG
		keypad: false,
        expressions: false
	});
    var expressions = JSON.parse($('#get_graph').text());
    var colors = JSON.parse($('#get_graph_color').text());
    for (var e = 0; e < expressions.length; e++){
        //dcg_new_expression(e, expressions[e]);
        graph.setExpression({id: e, latex: expressions[e], color: colors[e]});
    }
    dcg_set_graph_settings();
    refresh_char_colors('.dcg-template-mathquill');
    $('.dcg-template-mathquill').addClass('input_mathquill');
}

/**
 * Initialize the graph with given options and preferences and the given expressions from the server to be able to edit.
 */
function dcg_edit_graph(){
    $('#graph_container').html("");
	var elt = document.getElementById('graph_container');
	graph = Desmos.Calculator(elt, { //Set options for the DCG
		keypad: false,
        expressionsTopbar: false
	});
    var expressions = JSON.parse($('#get_graph').text());
    var colors = JSON.parse($('#get_graph_color').text());
    for (var e = 0; e < expressions.length; e++){
        graph.setExpression({id: e, latex: expressions[e], color: colors[e]});
    }
    dcg_set_graph_settings();
    dcg_refresh_variables();
    refresh_char_colors('.dcg-template-mathquill');
    $('.dcg-template-mathquill').addClass('input_mathquill');
    GRAPH_MODIFIED = true;
}

/**
 * This will update or create a new expression in the DCG. If the provided id already exists, the values for
 * the provided parameters will be updated in the expression (unprovided parameters will remain unchanged).
 * @param {String|number} id - The id of the expression you want to create or update.
 * @param {String|latex} expression - The LaTeX-expression
 */
function dcg_new_expression(id, expression) {
    graph.setExpression({id: id, latex: expression});
    var expr_cell = $('div[expr-id="'+id+'"]');
    expr_cell.find('.dcg-action-delete').remove();
    expr_cell.find('.dcg-template-dependentlabelhtml');
}

/**
 * This will update or create a new variable in the DCG. If the provided id already exists, the values for
 * the provided parameters will be updated in the variable (unprovided parameters will remain unchanged).
 * @param {String} id - The id of the variable you want to create or update.
 * @param {String} variable_name - The name of the variable.
 * @param {number} min - The minimum range of the variable.
 * @param {number} max - The maximum range of the variable.
 */
function dcg_new_variable(id, variable_name, min, max) {
    graph.setExpression({id: id, latex: variable_name + '=' + min, sliderBounds: {min: min, max: max, step: 0.1}});
    var variable_cell = $('div[expr-id="'+id+'"]');
    variable_cell.find('.dcg-action-delete').remove();
}

/**
 * Removes an specific expression from the expression list in the DCG.
 * @param {String} id - The id of the expression you want to delete.
 */
function dcg_remove_expression(id) {
    graph.removeExpression({id: id});
}

/**
 * Refreshes the variable-settings given from the domain-setter in the template-editor.
 * Automatically adds new variables and sets its range.
 */
function dcg_refresh_variables(){
    if(VARIABLE_COUNT > 0) {
        $('.opt_domain_from').each(function(){
            var i = $(this).attr('id').replace(/o_adv_from_/g, "");
            var name = VARIABLES[i];
            name = name[name.length -1];
            var from = $(this).val();
            if(from == ""){
                from = 1;
            }
            var to = $('#o_adv_to_' + i).val();
            dcg_new_variable('dcg_variable'+i, name, from, to);
        });
    }
    for(var key in dict_calc_unchanged){
        var char = "A";
        char = String.fromCharCode(char.charCodeAt(0) + parseInt(key));
        dcg_new_expression('dcg_variable_'+key, char+'='+dict_calc_unchanged[key]);
    }
    refresh_char_colors('.dcg-template-mathquill');
    $('.dcg-template-mathquill').addClass('input_mathquill');
}

/**
 * Sets a helper-expression which helps to monitor and react when the value of a normal expression or variable
 * changes in the expression-list.
 * @param {String} expression_name - The name of the variable or expression to monitor/react to.
 * @returns {Object} The helper-expression.
 */
function dcg_set_helper_expression(expression_name){
    helper_expression[expression_name] = graph.HelperExpression({latex: expression_name});
}

/**
 * Iterates through the expression-list and stores the expression in an list (sorts out the preset variables).
 * @returns {Object} An object with expressions (without preset variables).
 */
function dcg_get_expressions(){
    var expression_list = graph.getState()['expressions']['list'];
    var tmp_expr = [];
    var tmp_color = [];
    var expressions = {};
    for(var e = 0; e < expression_list.length; e++){
        if(expression_list[e]['id'].substring(0, 12) != 'dcg_variable'){
            tmp_expr.push(expression_list[e]['latex']);
            tmp_color.push(expression_list[e]['color']);
        }
    }
    expressions['latex'] = tmp_expr;
    expressions['color'] = tmp_color;
    window.console.log(expressions);
    return expressions;
}

/**
 * Retrieves the settings for the graph and return it as an object.
 * @returns {Object} The graph settings object.
 */
function dcg_get_graph_settings(){
    return graph.getState()['graph'];
}

/**
 * Retrieves and sets the graph-settings for the DCG.
 */
function dcg_set_graph_settings(){
    var settings = JSON.parse($('#get_graph_settings').text());
    var viewport = settings['viewport'];
    delete settings['viewport'];
    delete settings['squareAxes'];
    graph.setGraphSettings(settings);
    graph.setViewport([viewport['xmin'], viewport['xmax'], viewport['ymin'], viewport['ymax']]);
}