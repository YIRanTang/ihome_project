function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(document).ready(function() {
    $("#mobile").focus(function(){
        $("#mobile-err").hide();
    });
    $("#password").focus(function(){
        $("#password-err").hide();
    });
    $(".form-login").submit(function(e){
        // 干掉默认的表单提
        e.preventDefault();
        mobile = $("#mobile").val();
        passwd = $("#password").val();

        if (!mobile) {
            $("#mobile-err span").html("请填写正确的手机号！");
            $("#mobile-err").show();
            return;
        }
        if (!passwd) {
            $("#password-err span").html("请填写密码!");
            $("#password-err").show();
            return;
        }
        var req_data = {
            mobile:mobile,
            password:passwd
        }
        var req_json = JSON.stringify(req_data)
        $.ajax({
            url:"/api/v1_0/sessions",
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
                    location.href = "/index.html"
                }else{
                    alert(resp.errmsg)
                }
            }

        })

    });
})