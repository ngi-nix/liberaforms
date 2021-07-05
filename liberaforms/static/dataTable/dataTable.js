/*
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
*/

/* Table pinning idea seen at http://foundation.zurb.com */
/* Table card idea seen at https://www.exeideas.com/2020/10/simple-responsive-html-table.html */


function dataTable(options) {
  var table_id = options.table_id
  var csrftoken = options.csrftoken
  var items_endpoint = options.items_endpoint
  var item_endpoint = options.item_endpoint
  var edit_mode = options.edit_mode
  var switched = false;
  var paginate_page = 1;
  var retrieved_items = 0;
  var total_items = 0;

  var table = $("#" + table_id)
  table.addClass("lb-data-table")
  retrieve_items(); // make ajax request and populate table with result

  //
  /* ~~~~~~~~~~ setup layout ~~~~~~~~~~ */
  //

  /* ~~~~~~ add search input ~~~~~~~ */
  var search = $('<div class="input-group mb-3">')
  var input = $('<input type="text" class="form-control" \
                        aria-label="Search" \
                        aria-describedby="basic-addon2">')
  var group2 = $('<div class="input-group-append">')
  var button1 = $('<button class="btn clear_search" \
                          type="button" \
                          table="'+table_id+'">')
  var button2 = $('<button class="btn btn-primary search_items" \
                          type="button" \
                          table="'+table_id+'">')
  button1.html('Clear')
  button2.html('Search').append('<i class="fa fa-search" aria-hidden="true">')
  search.append(input)
  group2.append(button1)
  group2.append(button2)
  search.append(group2)
  search.insertBefore(table)

  /* ~~~~~~ add 'load more items' button ~~~~~~~ */
  var btn = $("<button class='btn btn-primary retrieve_items_button' \
                       table="+table_id+">")
  btn.html("Load more")
  btn.insertAfter(table);

  if (edit_mode) {
    $.jConfirm.defaults.question = 'Are you sure?';
    $.jConfirm.defaults.confirm_text = 'Delete';
    $.jConfirm.defaults.deny_text = 'Cancel';
    $.jConfirm.defaults.theme = 'bootstrap-4-white';
    $.jConfirm.defaults.position = 'right';
    $.jConfirm.defaults.size = 'small';
  }

  //
  /* ~~~~~~~~~~ events ~~~~~~~~~~ */
  //

  $(window).on("redraw",function(){
    switched=false;
    cards_to_grid();
    redraw_grid_table();
  });
  $(window).on("resize", function(){
    cards_to_grid();
    redraw_grid_table();
  });
  $(document).on("click", ".toggle-card", function(){
    if ($(this).hasClass('fa-chevron-circle-down')){
      var tr = $(this).closest('tr')
      $(tr).find('td').css('display', 'inline-block')
      $(this).removeClass('fa-chevron-circle-down')
             .addClass('fa-chevron-circle-up')
    } else {
      var tr = $(this).closest('tr')
      $(tr).find('td').css('display', '')
      $(tr).css('margin-bottom', '')
      $(this).removeClass('fa-chevron-circle-up')
             .addClass('fa-chevron-circle-down')
    }
  });
  $(document).on("click", ".mark_answer", function(){
    answer_id = $(this).closest('tr').attr('_id')
    mark_answer(answer_id)
  });
  $(document).on("confirm", ".delete-row", function(){
    answer_id = $(this).closest('tr').attr('_id')
    delete_answer(answer_id)
  });
  $(document).on("click", '.retrieve_items_button[table='+table_id+']', function(){
    retrieve_items()
  });
  $(document).on("click", '.clear_search[table='+table_id+']', function(){
    $(this).closest('.input-group').find('input').val('')
    clear_search();
  });
  $(document).on("click", '.search_items[table='+table_id+']', function(){
    if (retrieved_items < total_items) {
      retrieve_items(all_items=true)
    }
    var text = $(this).closest('.input-group').find('input').val()
    search_text(text);
  });
  /*
  $('.lb-data-table').on('mousedown', function(e) {
    console.log("mouse down")
    $('.lb-data-table').on('mousemove', function(evt) {
      console.log("mouse move")
      $('html,body').stop(false, true).animate({
          scrollLeft: evt.pageX - evt.clientX
      });
    });
  });
  $('.lb-data-table').on('mouseup', function() {
    $('.lb-data-table').off('mousemove');
  });
  */


  //
  /* ~~~~~~~~~~ responsive table ~~~~~~~~~~ */
  //

  function redraw_grid_table () {
    //console.log("redwaw grid table")
    if ($(window).width() <= 768) {
      if (switched) {
        unsplit_grid_table();
      }
      table.css('opacity', 1);
      return
    }
    if (!switched && HScrollVisible()) {
      split_grid_table();
    }
    else if (switched && HScrollVisible() == false) {
      unsplit_grid_table();
    }
    table.css('opacity', 1);
  }
  function cards_to_grid() {
    if ($(window).width() >= 768 && $(".pinned-table").length == 0) {
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
  function split_grid_table()
  {
    //console.log("split grid table")
    switched = true;
    var original = table
    if (original.parent(".responsive-table").length == 0) {
  	  original.wrap("<div class='responsive-table' />");
    }
    var pinned_table = create_pinned_table();
    //console.log(pinned_table)
    original.addClass('hidden-for-pin');
  	original.closest(".responsive-table").append(pinned_table);
  	original.wrap("<div class='scrollable' />");
  }
  function unsplit_grid_table() {
    switched = false;
    var original = table
    original.removeClass('hidden-for-pin');
    original.closest(".responsive-table").find(".pinned-table").remove();
    original.unwrap('.scrollable');
  }

  //
  /* ~~~~~~~~~~ table construction ~~~~~~~~~~ */
  //

  function create_pinned_table(){
    //console.log("create pinned table")
    var original = table;
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
    copy.find("tbody").find("tr").each(function(index, tr) {
      var newRow = $("<tr></tr>");
      newRow.attr('_id', $(tr).attr('_id'))
      first_td = $(this).find("td:first-child").clone()
      if (first_td.find('i.delete-row').length != 0) {
        first_td.find('i.delete-row').jConfirm()
      }
      first_td.appendTo(newRow);
      $(this).find("td:nth-child(2)").clone().appendTo(newRow);
      $(tbody).append(newRow);
    });
    return pinned_table;
  }
  function set_card_titles() {
    table.find('tr').each(function(i, tr) {
      var card_title = $(tr).find('td:eq(1)').html();
      var span = $(tr).find('td.row-controls').find('span.card-title')
      if (span.length == 0) {
        var card_title = $('<span class="card-title">'+card_title+'</span>')
        $(tr).find('.row-controls').append(card_title)
      }
    });
  }
  function insert_thead(fields) {
    var row = $('<tr>')
    for (let key in fields) {
      if (fields[key].name == "created") {
        var created_label = fields[key].label
        continue;
      }
      row.append('<th title="'+fields[key].label+'">'+fields[key].label+'</th>')
    }
    row.append('<th>'+created_label+'</th>')
    table.prepend($('<thead>').append(row))
  }
  function insert_items(data) {
    var tbody = table.find('tbody')
    if (tbody.length == 0) {
      tbody = $('<tbody>')
      table.append(tbody)
    }
    var fields = data.meta.field_index
    var items = data.items
    for (let item_key in items) {
      var item = items[item_key]
      var tr = $('<tr _id="'+item.id+'">')
      for (let field_key in fields) {
        var field = fields[field_key]
        if (field.name == "created") {
          var created_value = item.created
          var created_label = field.label
          continue;
        }
        if (field.name == "marked") {
          var td = $('<td class="row-controls">')
          var i = $('<i class="toggle-card action fa fa-chevron-circle-down" \
                        aria-label="Show fields">')
          td.append(i)
          if (edit_mode) {
            var i = $('<i class="fa fa-trash action delete-row" \
                          aria-label="Delete answer">')
            td.append(i.jConfirm())
          }
          var btn = $('<button class="btn btn-xs mark_answer">')
          btn.html('Mark <i class="fa fa-thumb-tack" \
                            aria-hidden="true"></i>')
          if ( item[field.name] == true ) {
            btn.addClass('btn-success')
          }
          td.append(btn)
        }
        else if (field.name.startsWith('file-')) {
          var td = $('<td class="dontEdit" data-label="'+field.label+'" \
                          aria-hidden="true">')
          td.html(item.data[field.name])
        }
        else {
          var td = $('<td data-label="'+field.label+'" aria-hidden="true">')
          td.html(sanitizeHTML(item.data[field.name]))
          if (edit_mode) {
            td.attr('type', field.name)
          }
        }
        tr.append(td)
      }
      var td = $('<td data-label="'+created_label+'" aria-hidden="true">')
      if (created_value.includes("T")) {
        var date_parts = created_value.split("T")
        var date = date_parts[0];
        var time = date_parts[1].split(".")[0]
        td.prop('title', date+' '+time)
        td.html(date + ' <span class="answer-time">'+time+'</span>')
      } else {
        td.html(created_value)
      }
      tr.append(td)
      tbody.append(tr)
    }
    set_card_titles();

    if (table.closest('.responsive-table').find("table.pinned-table").length !=0) {
      //console.log("replace pinned table")
      table.closest('.responsive-table').find("table.pinned-table")
           .replaceWith(create_pinned_table());
    }
    redraw_grid_table();
  }

  //
  /* ~~~~~~~~~~ ajax ~~~~~~~~~~ */
  //

  async function retrieve_items(all_items=false) {
    if (all_items) {
      var url = items_endpoint
    } else {
      var url = items_endpoint+"?page="+paginate_page
    }
    $.ajax({
      url : url,
      type: "GET",
      beforeSend: function(xhr, settings) {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type)) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken)
        }
      },
      success: function(data, textStatus, jqXHR)
      {
        if (table.find('thead').length == 0 ) {
          insert_thead(data.meta.field_index)
        }
        insert_items(data);
        paginate_page = paginate_page +1;
        retrieved_items = retrieved_items + data.items.length;
        total_items = data.meta.total
        if (retrieved_items < total_items) {
          $('.retrieve_items_button[table='+table_id+']').show()
        } else {
          $('.retrieve_items_button[table='+table_id+']').hide()
        }
      }
    });
  }
  function mark_answer(answer_id) {
    $.ajax({
      url : item_endpoint+'/'+answer_id+'/mark',
      type: "POST",
      beforeSend: function(xhr, settings) {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type)) {
          xhr.setRequestHeader("X-CSRFToken", csrftoken)
        }
      },
      success: function(data, textStatus, jqXHR)
      {
        buttons = $(document).find('tr[_id='+answer_id+']')
                             .find('button.mark_answer')
        if (data.marked == true) {
          $(buttons).removeClass("btn-basic").addClass("btn-success")
        }else{
          $(buttons).removeClass("btn-success").addClass("btn-basic")
        }
      }
    });
  }
  function delete_answer(answer_id) {
    var rows = $(document).find('tr[_id='+answer_id+']')
    rows.addClass('deletion-in-progress')
    $.ajax({
      url : item_endpoint+'/'+answer_id+'/delete',
      type: "DELETE",
      beforeSend: function(xhr, settings) {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type)) {
          xhr.setRequestHeader("X-CSRFToken", csrftoken)
        }
      },
      success: function(data, textStatus, jqXHR)
      {
        if (data.deleted == true) {
          rows.remove()
        }else{
          rows.removedClass('deletion-in-progress')
        }
      }
    });
  }

  //
  /* ~~~~~~~~~~ search functions ~~~~~~~~~~ */
  //

  function search_text(text) {
    if (text ==="") {
      $(table).find('tbody').find('tr').removeClass('not_found_by_search')
    } else {
      $(table).find('tbody').find('tr').each(function(i, tr) {
        var _id = $(tr).attr('_id')
        if ($(tr).is(':contains("'+text+'")')) {
          $(document).find('tr[_id='+_id+']').removeClass('not_found_by_search')
        } else {
          $(document).find('tr[_id='+_id+']').addClass('not_found_by_search')
        }
      });
    }
  }
  function clear_search() {
    table.find('tbody').find('tr').removeClass('not_found_by_search')
    table.closest('.responsive-table').find('.pinned-table')
                                      .find('tr')
                                      .removeClass('not_found_by_search')
  }
}

//
/* ~~~~~~~~~~ helper functions ~~~~~~~~~~ */
//

var HScrollVisible = function () {
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
var sanitizeHTML = function (str) {
   var temp = document.createElement('div');
   temp.textContent = str; return temp.innerHTML;
};
// makes 'contains' case insentive
jQuery.expr[':'].contains = function(a, i, m) {
  return jQuery(a).text().toUpperCase().indexOf(m[3].toUpperCase()) >= 0;
};
