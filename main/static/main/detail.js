$(document).on('click', '#like-button', function (e) {
    //$(document).on('click', '#like-button', (function (e) {
      //  console.log('Clicked');
    console.log($('#like-button').val())
    e.preventDefault();
    $.ajax({
            type: 'POST',
            url: '/like_bb/',
            data: {
                bb_id: $('#like-button').val(),
                csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val(),
                action: 'post'
            },
            success: function (json) {
                document.getElementById("like-button").innerHTML = json['result']
            }

        })
    });