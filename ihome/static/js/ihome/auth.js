function showSuccessMsg() {
    $('.popup_con').fadeIn('fast', function () {
        setTimeout(function () {
            $('.popup_con').fadeOut('fast', function () {
            });
        }, 1000)
    });
}

function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}
$(document).ready(function () {
    $("#real-name").readonly = "readonly"
    $.ajax({
        url: "/api/v1_0/users/auth",
        type: "get",
        dataType: "json",
        success: function (resp) {
            if (resp.errno == 0) {
                $("#real-name").val(resp.data.real_name)
                $("#id-card").val(resp.data.id_card)
                if(resp.data.real_name && resp.data.id_card){
                    $("#real-name").prop("disabled",true)
                    $("#id-card").prop("disabled",true)
                    $(".btn").prop("disabled",true)
                }

            } else if(resp.errno == "4003"){
                console.log("已实名认证")
            }
            else {
                alert(resp.errmsg)
            }


        }
    })
    $("#form-auth").submit(function (e) {
        e.preventDefault();

        // 干掉默认的表单提
        e.preventDefault();
        var real_name = $("#real-name").val();
        var id_card = $("#id-card").val();

        if (!real_name) {
            $(".error-msg").show();
            return;
        }
        if (!id_card) {
            $(".error-msg").show();
            return;
        }
        var req_data = {
            real_name:real_name,
            id_card:id_card
        }
        var req_json = JSON.stringify(req_data)
        $.ajax({
            url:"/api/v1_0/users/auth",
            type:"POST",
            contentType:"application/json",
            data:req_json,
            dataType:"json",
            // 自定义请求头
            headers:{
                "X-CSRFToken":getCookie("csrf_token")
            },
            success:function (resp) {
                if(resp.errno == 0){
                    showSuccessMsg()
                }else{
                    alert(resp.errmsg)
                }
            }

        })
    })
})