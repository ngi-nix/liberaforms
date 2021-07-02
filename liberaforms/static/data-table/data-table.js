
function HScrollVisible () {
  var table_width = 0;
  $("table.lb-data-table").each(function(i, table) {
    if ($(table).width() > table_width) {
      table_width = $(table).width();
    }
    console.log("table: "+table_width)
  });
  if (table_width > $(window).width()) {
    return true;
  }
  /*console.log("window: "+$(window).width())*/
  return false;
}

$(document).ready(function() {
  var switched = false;
  var updateTables = function() {
    //console.log(HScrollVisible())
    if (!switched && HScrollVisible() == true) {
      //console.log("splitting for Hscroll")
      splitAll();
    }
    else if (switched && HScrollVisible() == false) {
      //console.log("un-splitting for Hscroll")
      unsplitAll();
    }
    $("table.lb-data-table").each(function(i, element) {
      $(element).css('opacity', 1);
    });

    /*
    if (!switched && ($(window).width() < 767) ){
      splitAll();
    }
    else if (switched && ($(window).width() > 767)) {
      unsplitAll();
    }
    */
  };
  updateTables();
  function splitAll() {
    switched = true;
    $("table.lb-data-table").each(function(i, element) {
      splitTable($(element));
    });
    return true;
  }
  function unsplitAll() {
    switched = false;
    $("table.lb-data-table").each(function(i, element) {
      unsplitTable($(element));
    });
  }

  $(window).on("redraw",function(){switched=false; updateTables();}); // An event to listen for
  $(window).on("resize", updateTables);

	function splitTable(original)
	{
    console.log('splitTable')
		original.wrap("<div class='responsive-table' />");

		var copy = original.clone();
		copy.removeClass("lb-data-table");

    var pinned_table = $("<table class='pinned-table' />")
    var thead_row = copy.find("thead").find("tr");
    var newRow = $("<tr></tr>");
    $(thead_row).find("th:first-child").clone().appendTo(newRow);
    $(thead_row).find("th:nth-child(2)").clone().appendTo(newRow);
    $(pinned_table).append($('<thead />').append(newRow));
    copy.find("tbody").find("tr").each(function(index) {
        var newRow = $("<tr></tr>");
        $(this).find("td:first-child").clone().appendTo(newRow);
        $(this).find("td:nth-child(2)").clone().appendTo(newRow);
        $(pinned_table).append($('<tbody />').append(newRow));
    });
    //console.log(pinned_table)
    original.addClass('hidden-for-pin');
		original.closest(".responsive-table").append(pinned_table);
		original.wrap("<div class='scrollable' />");
	}

	function unsplitTable(original) {
    //console.log("unsplit table")
    original.removeClass('hidden-for-pin');
    original.closest(".responsive-table").find(".pinned-table").remove();
    original.unwrap('.scrollable');
	}

});
