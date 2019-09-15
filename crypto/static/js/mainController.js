var main = angular
	.module('main', [])
	.controller('mainController', ['$scope', mainController])
	.directive('ngTitle', function($parse) {
		return {
			restrict: "A",
			link: function(scope, element, attr) {
				scope.$watch(attr.ngTitle, function (v) {
					element.tooltip({
						title: v
					})
				});
			}
		};
	});

function mainController($scope) {
	vm = this;
	var dateFormat = "M/DD/YY h:mm A";
	vm.isCustom  = false;
	vm.toggleBar = true;
	vm.loaded 	 = true;
	vm.ut = moment().utc().format('HH:mm:ss');
	vm.hk = moment().tz('Asia/Hong_Kong').format('HH:mm:ss');
	vm.addrs = []
	vm.known = []
	vm.categories = []

	vm.formState   = "";
	vm.overlay     = {};
	vm.addrInput   = {};
	vm.filterInput = {};

	vm.tempAddr = {
		addr: '',
		url: ''
	};

	vm.customGraph = function () {
		vm.isCustom = true;
		resetSideBar();
		vm.tempAddr = {
			addr: '',
			url: ''
		};	
		$("#Home").collapse("show");
	}

	vm.customOff = function () {
		vm.isCustom = false;
		vm.addrs = [];
	}

	vm.toggleSide = function () {
		var onComplete;
		if (vm.toggleBar) {
			var sWidth = $('#sidebar-container').width();
			$('#sidebar-container').width(sWidth);
			$('#sidebar-container').removeClass('col-2');
			onComplete = () => {
				vm.toggleBar = false;
				$('#collapseBtn').removeClass('dropleft').addClass('dropright');
				$('#frame').removeClass('col');
				$('#iframe1').addClass('fixFrame');
			}
		} else {
			$('#frame').addClass('col');
			$('#iframe1').removeClass('fixFrame');
			onComplete = () => {
				vm.toggleBar = true;
				$('#collapseBtn').removeClass('dropright').addClass('dropleft');
				$('#sidebar-container').addClass('col-2');
			}
		}
		$('#sidebar-container').animate({
			width: 'toggle'
		}, 'slow', onComplete);
	}

	vm.makeGraph = function () {
		if (vm.addrs.length <= 1) return;
		var url = window.location + "/search/c?addr[]=" + vm.addrs[0];
		for (var i = 1; i < vm.addrs.length; i++) {
			url += "&addr[]=" + vm.addrs[i];
		}
		vm.startLoader();
		$('#iframe1').attr('src', url);
		vm.customOff();
	}

	vm.toggle = function (addr) {
		if ($(`#${addr}`).css('color') == 'rgb(255, 255, 255)') {
			$(`#${addr}`).css("color", '#495057');
			for (var i = 0; i < vm.addrs.length; i++) {
				if (vm.addrs[i] == addr) {
					vm.addrs.splice(i, 1);
				}
			}
		} else {
			vm.addrs.push(addr);
			$(`#${addr}`).css("color", 'rgb(255, 255, 255)');
		}
	}

	vm.showOverlay = function (obj) {
		$('#overlay').modal('show');
		$(".alert").remove();
		vm.overlay = obj;

		vm.addrInput = {
			addr: {
				val: '',
				state: 'invalid',
				reason: 'Invalid USDT Address!'
			},
			name: {
				val: '',
				state: 'invalid',
				reason: 'Must contain 3 or more characters!'
			},
			cat: {
				val: '',
				state: 'invalid',
				reason: 'Must contain 3 or more characters!'
			}
		};

		vm.filterInput = JSON.parse(JSON.stringify(dFilters));
		vm.filterInput['minTx'] = numberWithCommas(1000000); // 1 Mil
		vm.filterInput.minTime = "";
		vm.filterInput.maxTime = "";

		vm.filterInput['state'] = 'invalid';

		if (obj.type == "edit" || obj.type == "editCat") {
			if (obj.type == "edit") {
				vm.addrInput.name.val  = obj.name;
				vm.addrInput.name.state = 'valid';
			}
			
			vm.addrInput.cat.val   = obj.cat;
			vm.addrInput.cat.state = 'valid';

			var urlObj = new URL(location.href.replace("/usdt", "") + obj.url);
			for (filter in vm.filterInput) {
				if (obj.url.includes(filter)) {
					vm.filterInput[filter] = numberWithCommas(urlObj.searchParams.get(filter));
				}
			}
		} else if (obj.type == "add" && obj.addr) {
			vm.addrInput.addr.val  = obj.addr;
			vm.checkAddr();
		}
		
		$(function () {
			$('[data-toggle="tooltip"]').tooltip();

			$('input[name="minTime"]').daterangepicker({
				singleDatePicker: true,
				timePicker: true,
				showDropdowns: true,
				autoUpdateInput: false,
				opens: "center",
				parentEl: "#overlay",
				minDate: moment.unix(dFilters.minTime).format(dateFormat),
				maxDate: moment().format(dateFormat),
				locale: {
					format: dateFormat,
					cancelLabel: 'Clear'
				}
			});
			$('input[name="maxTime"]').daterangepicker({
				singleDatePicker: true,
				timePicker: true,
				showDropdowns: true,
				autoUpdateInput: false,
				drops: "up",
				opens: "center",
				parentEl: "#overlay",
				minDate: moment.unix(dFilters.minTime).format(dateFormat),
				locale: {
					format: dateFormat,
					cancelLabel: 'Clear'
				}
			});

			$('input[name="minTime"]').on('apply.daterangepicker', function(ev, picker) {
				setTime('minTime', picker.startDate.format(dateFormat));
			});

			$('input[name="maxTime"]').on('apply.daterangepicker', function(ev, picker) {
				setTime('maxTime', picker.startDate.format(dateFormat));
			});
		  
			$('input[name="minTime"]').on('cancel.daterangepicker', function() {
				setTime('minTime', 'oldest');
			});

			$('input[name="maxTime"]').on('cancel.daterangepicker', function() {
				setTime('maxTime', 'latest');
			});

			if (dFilters['minTime'] != "oldest") {
				vm.filterInput.minTime = moment.unix(dFilters['minTime']).format(dateFormat);
			} else {
				vm.filterInput.minTime = "oldest";
			}
			
			if (dFilters['maxTime'] != "latest") {
				vm.filterInput.maxTime = moment.unix(dFilters['maxTime']).format(dateFormat);
			} else {
				vm.filterInput.maxTime = "latest";
			}
		});
	}

	// REVIEW TIME
	function setTime(f, time) {
		$scope.$apply(function() {
			vm.filterInput[f] = time;
		});
	}


	/* REVIEW FOCUS AND BLUR CHECKS
	vm.addrFocusCheck = function (prop) {
		let val = vm.addrInput[prop].val;

		if (vm.overlay[prop] == val) {
			vm.addrInput[prop].val = "";
		}
	}

	vm.addrBlurCheck = function (prop) {
		if (vm.addrInput[prop].val == "") {
			vm.addrInput[prop].val = vm.overlay[prop];
		}
	}
	*/

	vm.filterFocusCheck = function (filter) {
		let val = vm.filterInput[filter].toString();
		if (/*dFilters[filter] == val.replace(/,/g, "") ||*/ val == "max" || val == "min" || val == "oldest" || val == "latest") {
			vm.filterInput[filter] = "";
		}
	}

	vm.filterBlurCheck = function (filter) {
		if (vm.filterInput[filter] == "") {
			vm.filterInput[filter] = numberWithCommas(dFilters[filter]);
		}
	}

	setInterval(function () {
		$scope.$apply(function () {
			vm.ut = moment().utc().format('HH:mm:ss');
			vm.hk = moment().tz('Asia/Hong_Kong').format('HH:mm:ss');
		});
	}, 1000);

	vm.submit = async function (type) {
		$(".alert").remove();
		vm.formState = "load";

		for (let filter in vm.filterInput) {
			$(`input[name='${filter}']`).val(vm.filterInput[filter].toString().replace(/,/g, ""));
		}

		let resp = await $.ajax({
			url: $(`#${type}`).attr('action'),
			type: 'POST',
			data: $(`#${type}`).serialize()
		});

		vm.formState = "";

		console.log(resp);

		if (resp.toLowerCase() == "success") {
			updateKnown();
			$(`.modal`).modal('hide');
		} else {
			$("#overlay").prepend('<div class="alert alert-danger alert-dismissible fade show" role="alert"><strong>Error!</strong> You should check in on some of those fields below.<button type="button" class="close" data-dismiss="alert" aria-label="Close">&times;</button></div>')
		}

		/*
		for (let filter in vm.filterInput) {
			vm.filterInput[filter] = numberWithCommas(vm.filterInput[filter]);
		}
		*/
	}

	async function updateKnown() {
		vm.known = await $.get(window.location + "/getKnown");
		vm.categories = [];
		for (var i = 0; i < vm.known.length; i++) {
			vm.categories.push(vm.known[i].category);
		}
	}

	vm.checkAddr = async function () {
		$('.tooltip').remove();
		var val = vm.addrInput.addr.val;
		var valid = false;

		if (val.length == 34 && !val.includes(" ") && addrPattern.test(val)) {
			vm.addrInput.addr.state = "load";
			let isValid = await isValidAddr(val);

			if (isValid) {
				var addrs = $(".addr");
				var exists = false;
				var i = 0;

				while (i < addrs.length && !exists) {
					if ($(addrs[i]).attr("data-addy") == val) {
						exists = true;
					}

					i++;
				}

				if (!exists) {
					valid = true;
				}
			}
		}

		if (valid) {
			vm.addrInput.addr.state = "valid";
		} else {
			vm.addrInput.name.reason = "Invalid USDT Address!";
			vm.addrInput.addr.state = "invalid";
		}
	}

	vm.checkName = function () {
		$('.tooltip').remove();
		var val   = vm.addrInput.name.val;
		var valid = false;

		if (val.length <= 16 && val.length > 2 && namePattern.test(val)) {

			vm.addrInput.name.state = "load";

			var addrs = $(".addr");
			var exists = false;
			var i = 0;

			while (i < addrs.length && !exists) {
				if ($(addrs[i]).text().trim().toLowerCase() == val.toLowerCase() && $(addrs[i]).attr("data-addy") != vm.overlay.addr) {
					exists = true;
				}

				i++;
			}

			if (!exists) {
				valid = true;
			}
		} else if (val.length > 16) {
			vm.addrInput.name.reason = "Must only contain 16 characters or less!";
		} else if (val.length < 3) {
			vm.addrInput.name.reason = "Must contain 3 or more characters!";
		} else if (!namePattern.test(val)) {
			vm.addrInput.name.reason = "Must only contain numbers or letters!";
		}

		if (valid) {
			vm.addrInput.name.state = "valid";
		} else {
			vm.addrInput.name.state = "invalid";
		}
	}

	vm.checkCat = function () {
		$('.tooltip').remove();
		var val   = vm.addrInput.cat.val;
		var valid = false;

		if (val.length < 16 && val.length > 2 && namePattern.test(val)) {
			valid = true;
		} else if (val.length > 16) {
			vm.addrInput.cat.reason = "Must only contain 16 characters or less!";
		} else if (val.length < 3) {
			vm.addrInput.cat.reason = "Must contain 3 or more characters!";
		} else if (!namePattern.test(val)) {
			vm.addrInput.cat.reason = "Must only contain numbers or letters!";
		}

		if (valid) {
			vm.addrInput.cat.state = "valid";
		} else {
			vm.addrInput.cat.state = "invalid";
		}
	}

	vm.startLoader = function() { 
		vm.loaded = false;
		$('iframe').contents().find('body').html("");
	}

	$('iframe').on('load', function() {
		$scope.$apply(function() {
			vm.loaded = true;
		});
	});

	function numberWithCommas(x) {
		var parts = x.toString().split(".");
		parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
		return parts.join(".");
	}

	vm.addCommas = function(name) {
		var prevVal = vm.filterInput[name].replace(/,/g, "");

		if (prevVal == "" || Number.isNaN(parseFloat(prevVal)) || (!isNaN(prevVal) && prevVal[prevVal.length - 1] == ".")) {
			return;
		}

		vm.filterInput[name] = numberWithCommas(prevVal);
	}

	updateKnown();
}