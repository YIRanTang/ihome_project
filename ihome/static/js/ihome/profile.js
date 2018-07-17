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
    // 加载页面请求信息
    $.ajax({
        url: "/api/v1_0/users/avatar",
        type: "get",
        dataType: "json",
        success: function (resp) {
            if (resp.errno == 0) {
                $("#user-avatar").attr("src", resp.data.avatar_url)
                $("#user-name").val(resp.data.user_name)
            } else if (resp.errno == "4101") {
                location.href = "/"
            }
            else {
                alert(resp.errmsg)
            }
        }

    })

    $("#form-avatar").submit(function (e) {
        // 干掉默认的表单提
        e.preventDefault();
        $(this).ajaxSubmit({
            url: "/api/v1_0/users/avatar",
            type: "post",
            dataType: "json",
            // 自定义请求头
            headers: {
                "X-CSRFToken": getCookie("csrf_token")
            },
            success: function (resp) {
                if (resp.errno == 0) {
                    $("#user-avatar").attr("src", resp.avatar_url)
                } else if (resp.errno == "4101") {
                    location.href = "/"
                }
                else {
                    alert(resp.errmsg)
                }
            }
        });

    })

    $("#form-name").submit(function (e) {
        e.preventDefault();
        var name = $("#user-name").val()
        if(!name){
            alert("请填写用户名")
            return
        }

        $.ajax({
            url: "/api/v1_0/users/name",
            data:JSON.stringify({name:name}),
            type: "put",
            dataType: "json",
            contentType:"application/json",
            // 自定义请求头
            headers: {
                "X-CSRFToken": getCookie("csrf_token")
            },
            success: function (resp) {
                if (resp.errno == 0) {
                    showSuccessMsg()
                    $("#user-name").val(resp.data.name)
                } else if (resp.errno == "4101") {
                    location.href = "/"
                } else if(resp.errno == "4001"){
                    $(".error-msg").show()
                } else {
                    alert(resp.errmsg)
                }
            }
        });
    })
})
