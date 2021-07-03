/* Table pinning idea seen at http://foundation.zurb.com */
/* Table card idea seen at https://www.exeideas.com/2020/10/simple-responsive-html-table.html */

function HScrollVisible () {
  var table_width = 0;
  $("table.lb-data-table").each(function(i, table) {
    if ($(table).width() > table_width) {
      table_width = $(table).width();
    }
  });
  if (table_width > $(window).width()) {
    return table_width;
  }
  return false;
}

$(document).ready(function() {
  var switched = false;

  $(".show-card").on("click", function (){
    if ($(this).hasClass('fa-chevron-circle-down')){
      var tr = $(this).closest('tr')
      $(tr).find('td').css('display', 'block')
      $(tr).css('margin-bottom', '2em')
      $(this).removeClass('fa-chevron-circle-down')
             .addClass('fa-chevron-circle-up')
    } else {
      var tr = $(this).closest('tr')
      $(tr).find('td').not(':first').css('display', '')
      $(tr).css('margin-bottom', '')
      $(this).removeClass('fa-chevron-circle-up')
             .addClass('fa-chevron-circle-down')
    }
  });
  //console.log(HScrollVisible())

  function update_grid_tables () {
    if ($(window).width() <= 600) {
      if (switched) {
        unsplit_all_grid_tables();
      }
      $("table.lb-data-table").each(function(i, element) {
        $(element).css('opacity', 1);
      });
      return
    }
    if (!switched && HScrollVisible()) {
      split_all_grid_tables();
    }
    else if (switched && HScrollVisible() == false) {
      unsplit_all_grid_tables();
    }
    $("table.lb-data-table").each(function(i, element) {
      $(element).css('opacity', 1);
    });
  }

  update_grid_tables();
  function split_all_grid_tables() {
    switched = true;
    $("table.lb-data-table").each(function(i, element) {
      split_grid_table($(element));
      console.log("splitting")
    });
    return true;
  }

  function unsplit_all_grid_tables() {
    switched = false;
    $("table.lb-data-table").each(function(i, element) {
      usplit_grid_table($(element));
    });
  }

  function cards_to_grid() {
    if ($(window).width() >= 600 && $(".pinned-table").length == 0) {
      console.log('card to grid')
      $("table.lb-data-table").each(function(i, element) {
        $(element).find('tr').each(function (i, tr) {
          $(tr).find('td').css('display', '')
          $(tr).css('margin-bottom', '')
          $(tr).find('.fa-chevron-circle-up')
               .removeClass('fa-chevron-circle-up')
               .addClass('fa-chevron-circle-down')
        });
      });
    }
  }

  function split_grid_table(original)
  {
    console.log('split_grid_table')
    if (original.parent(".responsive-table").length == 0) {
  	   original.wrap("<div class='responsive-table' />");
    }

  	var copy = original.clone();
  	copy.removeClass("lb-data-table");

    var pinned_table = $("<table class='pinned-table' />")
    var thead_row = copy.find("thead").find("tr");
    var tbody = $('<tbody />');
    var newRow = $("<tr></tr>");
    $(thead_row).find("th:first-child").clone().appendTo(newRow);
    $(thead_row).find("th:nth-child(2)").clone().appendTo(newRow);
    $(pinned_table).append($('<thead />').append(newRow));
    $(pinned_table).append(tbody);
    copy.find("tbody").find("tr").each(function(index) {
        var newRow = $("<tr></tr>");
        $(this).find("td:first-child").clone().appendTo(newRow);
        $(this).find("td:nth-child(2)").clone().appendTo(newRow);
        $(tbody).append(newRow);
    });
    //console.log(pinned_table)
    original.addClass('hidden-for-pin');
  	original.closest(".responsive-table").append(pinned_table);
  	original.wrap("<div class='scrollable' />");
  }

  function usplit_grid_table(original) {
    //console.log("unsplit table")
    original.removeClass('hidden-for-pin');
    original.closest(".responsive-table").find(".pinned-table").remove();
    original.unwrap('.scrollable');
  }

  $(window).on("redraw",function(){switched=false; update_grid_tables();}); // An event to listen for
  $(window).on("resize", function(){ cards_to_grid(); update_grid_tables();});

});

$(document).ready(function() {

});
