jQuery('.dropdown-menu').click(function (e) {
    e.stopPropagation();
});

var prevVal = '';
var addrPattern = new RegExp(/[a-zA-Z0-9\b]$/);
var namePattern = new RegExp(/[a-zA-Z0-9\b_-]$/);

function numberWithCommas(x) {
    var parts = x.toString().split(".");
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    return parts.join(".");
}

$(document).ready(function () {
    $("#searchBar").on("keyup", async function () {
        var original = $(this).val();
        var value = original.toLowerCase();
        var vm = angular.element($('body')).scope();

        if (value == prevVal) return;

        prevVal = value;

        if (value === "") {
            resetSideBar();
            vm.$apply(`basic.tempAddr={addr:'',url:''}`);
            return;
        }

        var categories = {};
        var exists = false;
        $("#accordion .addr").filter(function () {
            let isValid = ($(this).text().toLowerCase().indexOf(value) > -1 || $(this).attr("data-addy").toLowerCase() === value);
            if (isValid) {
                categories[$(this).parent().parent().attr('id')] = true;
                exists = true;
            }
            $(this).toggle(isValid);
        });

        if (Object.keys(categories).length == 2 && categories['Home']) {
            categories['Home'] = false;
        } else if (Object.keys(categories).length > 2) {
            categories = {
                'Home': true
            }
        }

        $("#accordion .category").filter(function () {
            let toggle = categories[$(this).attr('name')] === true;

            if (toggle) {
                $('#' + $(this).attr('name')).collapse('show');
            }

            $(this).toggle(toggle);
        });

        /*
        if (Object.keys(categories).length == 1) {
            $(`[cat='${Object.keys(categories)[0]}']`).collapse('show');
        }
        */

        if (!exists && value.length == 34 && !value.includes(" ") && addrPattern.test(value)) {
            $('#spinner').show();
            let isValid = await isValidAddr(original);
            if (isValid) {
                $('#spinner').hide();
                vm.$apply(`basic.tempAddr={addr:'${original}',url:'${window.location.pathname + "/search/" + original}'}`);
            } else {
                $('#spinner').hide();
            }
        } else {
            vm.$apply(`basic.tempAddr={addr:'',url:''}`);
        }
    });
});

function resetSideBar() {
    $("#searchBar").val("");
    $("#accordion .addr").toggle(true)
    $("#accordion .category").filter(function () {
        if ($(this).attr('name') != "Home") {
            $('#' + $(this).attr('name')).collapse('hide');
        }

        $(this).toggle(true);
    });
    prevVal = '';
}

function isValidAddr(addr) {
    return new Promise(async resolve => {
        resolve(await $.get("./isValidAddr?addr=" + addr));
    });
}

var dragging = false,
    toggle = false;

$('#dragbar').mousedown(function (e) {
    e.preventDefault();
    dragging = true;
    var side = $('#sidebar-container');
    $('iframe').css('pointer-events', 'none');
    $(document).mousemove(function (ex) {
        if (ex.pageX + 2 < 425 && ex.pageX + 2 > 50 && dragging && !toggle) {
            side.width(ex.pageX + 2);
        } else if (ex.pageX + 2 <= 50 && !toggle && dragging) {
            toggle = true;
            stopDrag();
            $("#dragcircle i").attr("class", "fas fa-caret-left open");
            side.animate({
                width: '0px'
            }, 250);
        }

        if (side.width() < 85) {
            $(".btn-overlap").hide();
        } else {
            $(".btn-overlap").show();
        }
    });
});

$("#sidebar-container").hover(() => {
    if (!toggle) {
        $(".drag").addClass("slide-right");
    }
}, () => {
    if (!toggle) {
        $(".drag").removeClass("slide-right");
    }
});

$("#dragcircle").click(() => {
    var symbol = $("#dragcircle i");
    if (toggle) {
        $(symbol).attr("class", "fas fa-caret-left");
        $('#sidebar-container').animate({
            width: '250px'
        }, 'slow');
        toggle = false;
        $(".btn-overlap").show();
        $(".drag").removeClass("slide-right");
    } else {
        $(".btn-overlap").hide();
        $(".drag").addClass("slide-right");
        $(symbol).attr("class", "fas fa-caret-left open");
        $('#sidebar-container').animate({
            width: '0px'
        }, 'slow');
        toggle = true;
    }
});

function stopDrag() {
    $('iframe').css('pointer-events', 'auto');
    $(document).unbind('mousemove');
    dragging = false;
}

$(document).mouseup(function (e) {
    if (dragging) {
        stopDrag();
    }
});

function rotate(el) {
    el = $(el).find("i");
    if ($(el).hasClass("open")) {
        $(el).attr("class", "fas fa-caret-down");
    } else {
        $(".open").attr("class", "fas fa-caret-down");
        $(el).attr("class", "fas fa-caret-down open");
    }
}

$('#accordion').on('hide.bs.collapse', e => {
    var el = $(`[name='${e.target.id}']`).find('.fa-caret-down');

    $(el).attr("class", "fas fa-caret-down");
});

$('#accordion').on('show.bs.collapse', e => {
    var el = $(`[name='${e.target.id}']`).find('.fa-caret-down');

    $(el).attr("class", "fas fa-caret-down open");
});