
jQuery('.dropdown-menu').click(function (e) {
	e.stopPropagation();
});

var prevVal 	= '';
var addrPattern = new RegExp(/[a-zA-Z0-9\b]$/);
var namePattern = new RegExp(/[a-zA-Z0-9\b_-]$/);

$(document).ready(function () {
	$("#searchBar").on("keyup", async function () {
		var original = $(this).val();
		var value    = original.toLowerCase();

		if (value == prevVal) return;

		prevVal = value;

		var categories = {};
		var exists     = false;
		$("#accordion .addr").filter(function () {
			let isValid = ($(this).text().toLowerCase().indexOf(value) > -1 || $(this).attr("data-addy").toLowerCase() === value);
			if (isValid) {
				categories[$(this).parent().attr('id')] = true;
				exists = true;
			}
			$(this).toggle(isValid);
		});
		$("#accordion .category").filter(function () {
			$(this).toggle(categories[$(this).find('button').attr('aria-controls')] === true);
		});
		if (Object.keys(categories).length == 1) {
			$("#" + Object.keys(categories)[0]).collapse('show');
		}

		if (!exists && value.length == 34 && !value.includes(" ") && addrPattern.test(value)) {
			$('#spinner').show();
			let isValid = await isValidAddr(original);
			if (isValid) {
				$('#spinner').hide();
				let vm = angular.element($('body')).scope();
				vm.$apply(`vm.tempAddr={addr:'${original}',url:'${window.location + "/search/" + original}'}`);
			}
		} else {
			let vm = angular.element($('body')).scope();
			vm.$apply(`vm.tempAddr={addr:'',url:''}`);
		}
	});
});

function isValidAddr(addr) {
	return new Promise(async resolve => {
		resolve(await $.get(window.location + "/addr?method=isValid&addr=" + addr));
	});
}

var dragging = false, toggle = false;

$('#dragbar').mousedown(function(e) {
	e.preventDefault();
	dragging = true;
	var side = $('#sidebar-container');
	$('iframe').css('pointer-events', 'none');
	$(document).mousemove(function(ex) {
		if (ex.pageX + 2 < 400 && ex.pageX + 2 > 50 && dragging) {
			side.width(ex.pageX + 2);
		} else if (ex.pageX + 2 <= 50 && !toggle && dragging) {
			toggle = true;
			stopDrag();
			$("#dragcircle i").attr("class", "fas fa-caret-left open");
			side.animate({width: '0px'}, 250);
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
		$("#dragcircle").addClass("slide-right");
	}
}, () => {
	if (!toggle) {
		$("#dragcircle").removeClass("slide-right");
	}
});

$("#dragcircle").click(() => {
	console.log(toggle);
	var symbol = $("#dragcircle i");
	if (toggle) {
		$(symbol).attr("class", "fas fa-caret-left");
		$('#sidebar-container').animate({width: '250px'}, 'slow');
		toggle = false;
	} else {
		$("#dragcircle").addClass("slide-right");
		$(symbol).attr("class", "fas fa-caret-left open");
		$('#sidebar-container').animate({width: '0px'}, 'slow');
		toggle = true;
	}
})

function stopDrag() {
	$('iframe').css('pointer-events', 'auto');
	$(document).unbind('mousemove');
	dragging = false;
}

$(document).mouseup(function(e) {
	if (dragging) {
		stopDrag();
	}
});


function rotate(el) {
	el = $(el).find("i");
	if ($(el).hasClass("open")) {
		$(el).attr("class", "fas fa-caret-down");
	} else {
		$(el).attr("class", "fas fa-caret-down open");
	}
}