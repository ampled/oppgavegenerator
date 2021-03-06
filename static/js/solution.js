/**
 * Opens and draws all steps in solution.
 * Collapse and Un-collapse the panel by button-click.
 */
$(document).ready(function () {
    console.log('solution.js running solution step printer on document ready');
    // See step-by-step solution
    var v_solution = $('#v_solution');
    var v_panel = $('#v_panel');
    v_solution.click(function (e) {
        e.preventDefault();
        v_panel.fadeIn(function(){
            redraw_mathquill_elements();
            //$('.mathquill-rendered-math').mathquill('redraw'); // Redraws the latex math when it is shown.
        });
    });

    // Close step-by-step solution
    var v_ok = $('#v_ok');
    v_ok.click(function (e) {
        e.preventDefault();
        v_panel.fadeOut();
    });

    var solution = $('#get_solution').text();
    solution = solution.split('§');
    for(var s = 0; s < solution.length; s++){
        if(document.getElementById("mathquill_solution_" + s) == null){
                console.log('printing step' + s);
            $('#mathquill_field').append('<div class="input_field"><div id="mathquill_solution_' + s + '" class="static-math input_mathquill">' + solution[s] + '</div></div><br/>');
        }
        //$('#mathquill_solution_' + s).mathquill().mathquill('latex', solution[s]);
    }
    console.log('solution.js document ready done')
});

/**
 * When all elements are loaded after document-ready, we need to redraw mathquill-ified elements.
 */
//$(window).load(function(){
//   $('.mathquill-rendered-math').mathquill('redraw');
//});