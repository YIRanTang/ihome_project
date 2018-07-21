var param = {
    sk: "new",
    aid: "",
    sd: "",
    ed: ""
}
var cur_page = 1; // 当前页
var next_page = 1; // 下一页
var total_page = 1;  // 总页数
var house_data_querying = true;   // 是否正在向后台获取数据

function decodeQuery() {
    var search = decodeURI(document.location.search);
    return search.replace(/(^\?)/, '').split('&').reduce(function (result, item) {
        values = item.split('=');
        result[values[0]] = values[1];
        return result;
    }, {});
}

function updateFilterDateDisplay(a) {
    var startDate = $("#start-date").val();
    var endDate = $("#end-date").val();
    var $filterDateTitle = $(".filter-title-bar>.filter-title").eq(0).children("span").eq(0);
    if (startDate) {
        var text = startDate.substr(5) + "/" + endDate.substr(5);
        $filterDateTitle.html(text);
    } else {
        $filterDateTitle.html("入住日期");
    }
    param.sd = startDate
    param.ed = endDate
    //根据条件请求房屋数据
}
//action=="renew" 表示数据清空重新展示
function updateHouseData(action) {
    console.log(param)
    $.get("/api/v1_0/house/search", param, function (resp) {
        house_data_querying = false
        if (resp.errno == 0) {
            if (resp.data.tatol_count == 0) {
                $(".house-list").html("暂时没有符合您查询的房屋信息。")
            } else {
                total_page = resp.data.tatol_page
                house_html = template("house-item-temp", {houses: resp.data.houses});
                if (action == "renew") {
                    $(".house-list").html(house_html)
                } else {
                    cur_page = next_page
                    $(".house-list").append(house_html)
                }
            }


        } else {
            alert(resp.errmsg)
        }
    })
}

$(document).ready(function () {
    var queryData = decodeQuery();
    var startDate = queryData["sd"];
    var endDate = queryData["ed"];
    $("#start-date").val(startDate);
    $("#end-date").val(endDate);
    var areaName = queryData["aname"];
    if (!areaName) areaName = "位置区域";
    $(".filter-title-bar>.filter-title").eq(1).children("span").eq(0).html(areaName);

    // 获取地区
    $.get("/api/v1_0/areas", function (resp) {
        if (resp.errno == 0) {
            area_html = template("area-temp", {areas: resp.data.areas});
            $(".filter-area").html(area_html)
            param.aid = queryData["aid"]
            updateHouseData("renew")
            // 获取页面显示窗口的高度
            var windowHeight = $(window).height();
            // 为窗口的滚动添加事件函数
            window.onscroll = function () {

                // var a = document.documentElement.scrollTop==0? document.body.clientHeight : document.documentElement.clientHeight;
                var b = document.documentElement.scrollTop == 0 ? document.body.scrollTop : document.documentElement.scrollTop;
                var c = document.documentElement.scrollTop == 0 ? document.body.scrollHeight : document.documentElement.scrollHeight;
                // 如果滚动到接近窗口底部
                if (c - b < windowHeight + 50) {
                    // 如果没有正在向后端发送查询房屋列表信息的请求
                    console.log(house_data_querying)
                    if (!house_data_querying) {
                        // 将正在向后端查询房屋列表信息的标志设置为真，
                        house_data_querying = true;
                        // 如果当前页面数还没到达总页数
                        if (cur_page < total_page) {
                            // 将要查询的页数设置为当前页数加1
                            next_page = cur_page + 1;
                            // 向后端发送请求，查询下一页房屋数据
                            updateHouseData();
                        } else {
                            house_data_querying = false;
                        }
                    }
                }
            }

        } else {
            alert(resp.errmsg)
        }
    })


    $(".input-daterange").datepicker({
        format: "yyyy-mm-dd",
        startDate: "today",
        language: "zh-CN",
        autoclose: true
    });


    var $filterItem = $(".filter-item-bar>.filter-item");
    $(".filter-title-bar").on("click", ".filter-title", function (e) {
        var index = $(this).index();
        if (!$filterItem.eq(index).hasClass("active")) {
            $(this).children("span").children("i").removeClass("fa-angle-down").addClass("fa-angle-up");
            $(this).siblings(".filter-title").children("span").children("i").removeClass("fa-angle-up").addClass("fa-angle-down");
            $filterItem.eq(index).addClass("active").siblings(".filter-item").removeClass("active");
            $(".display-mask").show();
        } else {
            $(this).children("span").children("i").removeClass("fa-angle-up").addClass("fa-angle-down");
            $filterItem.eq(index).removeClass('active');
            $(".display-mask").hide();
        }
    });
    $(".display-mask").on("click", function (e) {
        $(this).hide();
        $filterItem.removeClass('active');
        cur_page = 1; // 当前页
        next_page = 1; // 下一页
        total_page = 1;  // 总页数
        house_data_querying = true;
        updateHouseData("renew")
    });
    $(".filter-item-bar>.filter-area").on("click", "li", function (e) {
        if (!$(this).hasClass("active")) {
            $(this).addClass("active");
            $(this).siblings("li").removeClass("active");
            $(".filter-title-bar>.filter-title").eq(1).children("span").eq(0).html($(this).html());
            param.aid = $(this).attr("area-id")

        } else {
            $(this).removeClass("active");
            $(".filter-title-bar>.filter-title").eq(1).children("span").eq(0).html("位置区域");
        }

    });
    $(".filter-item-bar>.filter-sort").on("click", "li", function (e) {
        if (!$(this).hasClass("active")) {
            $(this).addClass("active");
            $(this).siblings("li").removeClass("active");
            $(".filter-title-bar>.filter-title").eq(2).children("span").eq(0).html($(this).html());
            param.sk = $(this).attr("sort-key")

        }
    })
})