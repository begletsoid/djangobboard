$(document).ready(function(){
    console.log('asdasdasdasdasdasd')
    $(document).on('click', '#like_button', (function (e) {
        e.preventDefault();
        $.ajax({
            type: 'POST',
            url: '{% url "accounts:like_bb" %}',
            data: {
                postid: $('#like_button').val(),
                csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val(),
                atcion: 'post'
            },
            success: function (json) {
                document.getElementById("like_button").innerHTML = json['result']
            }

        })
    });

});