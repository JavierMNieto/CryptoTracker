
main.controller('premController', ['$scope', premController]);

main.directive('premController', function() {
	return {
		controller: 'premController',
		controllerAs: 'prem'
	}
});

function premController($scope) {
	var prem = this;

	var dateFormat = "M/DD/YY h:mm A";
	var addrTimeout;
	prem.overlay = {};
	prem.addrInput = {};
	prem.filterInput = {};
	prem.addrs = [];

	prem.showOverlay = function (obj) {
		$(".alert").remove();
		$scope.main.overlay = obj;

		prem.addrInput = {
			addr: {
				val: '',
				valid: false,
				reason: 'Invalid USDT Address!'
			},
			name: {
				val: '',
				valid: false,
				reason: 'Must contain 3 or more characters!'
			},
			cat: {
				val: '',
				valid: false,
				reason: 'Must contain 3 or more characters!'
			}
		};

		prem.filterInput = JSON.parse(JSON.stringify(dFilters));
		prem.filterInput['minTx'] = numberWithCommas(1000000); // 1 Mil

		prem.filterInput['valid'] = false;

		if (obj.type == "edit" || obj.type == "editCat") {
			if (obj.type == "edit") {
				prem.addrInput.name.val = obj.name;
				prem.addrInput.name.valid = true;
			}

			prem.filterInput.minTime = "";
			prem.filterInput.maxTime = "";

			prem.addrInput.cat.val = obj.cat;
			prem.addrInput.cat.valid = true;
		} else if (obj.type == "add" && obj.addr) {
			prem.addrInput.addr.val = obj.addr;
			prem.checkAddr();
		}

		$('#overlay').modal('show');
		
		$(function () {
			
			$('[data-toggle="tooltip"]').tooltip({
				trigger: "hover"
			});

			$('input[name="minTime"]').daterangepicker({
				singleDatePicker: true,
				timePicker: true,
				showDropdowns: true,
				autoUpdateInput: false,
				drops: "up",
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

			$('input[name="minTime"]').on('apply.daterangepicker', function (ev, picker) {
				setTime('minTime', picker.startDate.format(dateFormat));
			});

			$('input[name="maxTime"]').on('apply.daterangepicker', function (ev, picker) {
				setTime('maxTime', picker.startDate.format(dateFormat));
			});

			$('input[name="minTime"]').on('cancel.daterangepicker', function () {
				setTime('minTime', 'oldest');
			});

			$('input[name="maxTime"]').on('cancel.daterangepicker', function () {
				setTime('maxTime', 'latest');
			});

			if (obj.filters) {
				for (f in dFilters) {
					if (obj.filters[f] && typeof obj.filters[f] == "number") {
						if (f.includes("Time")) {
							if (obj.filters[f] < -1) {	
								var scale = getTimeScale(obj.filters[f]);

								if (scale) {
									var amt = -obj.filters[f] / conversionToSec[scale];
									scale = scale.charAt(0).toUpperCase() + scale.slice(1); // capitalize first letter

									if (amt == 1) {
										prem.filterInput[f] = "Last " + scale;
									} else {
										prem.filterInput[f] = `Last ${amt} ${scale}s`;
									}
								}
							} else {
								prem.filterInput[f] = moment.unix(obj.filters[f]).format(dateFormat);
							}
						} else {
							prem.filterInput[f] = numberWithCommas(obj.filters[f]);
						}
					} else {
						prem.filterInput[f] = dFilters[f];
					}
				}
			}
		});
	}

	prem.filterFocusCheck = function (filter) {
		let val = prem.filterInput[filter].toString();
		if ( /*dFilters[filter] == val.replace(/,/g, "") ||*/ val == "max" || val == "min" || val == "oldest" || val == "latest") {
			prem.filterInput[filter] = "";
		}
	}

	prem.filterBlurCheck = function (filter) {
		if (prem.filterInput[filter] == "") {
			prem.filterInput[filter] = numberWithCommas(dFilters[filter]);
		}
	}

	prem.checkAddr = function () {
		$('.tooltip').remove();
		var val = prem.addrInput.addr.val;
		var valid = false;

		if (val.length == 34 && !val.includes(" ") && addrPattern.test(val)) {
			valid = null;
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

			if (valid) {
				clearTimeout(addrTimeout);

				addrTimeout = setTimeout(async () => {
					$scope.$apply(() => {
						prem.addrInput.addr.valid = null;
					});
					let isValid = await isValidAddr(val);
					prem.addrInput.addr.valid = isValid;
					if (!isValid) {
						prem.addrInput.addr.reason = "Invalid USDT Address!";
					}
				}, 250);
			}
		}

		if (valid === false) {
			prem.addrInput.addr.valid = valid;
			prem.addrInput.name.reason = "Address has already been added!";
		}
	}

	prem.checkName = function () {
		$('.tooltip').remove();
		var val = prem.addrInput.name.val;
		var valid = false;

		if (val.length <= 16 && val.length > 2 && namePattern.test(val)) {

			prem.addrInput.name.valid = null;

			var addrs = $(".addr");
			var exists = false;
			var i = 0;

			while (i < addrs.length && !exists) {
				if ($(addrs[i]).text().trim().toLowerCase() == val.toLowerCase() && $(addrs[i]).attr("data-addy") != prem.overlay.addr) {
					exists = true;
				}

				i++;
			}

			if (!exists) {
				valid = true;
			}
		} else if (val.length > 16) {
			prem.addrInput.name.reason = "Must only contain 16 characters or less!";
		} else if (val.length < 3) {
			prem.addrInput.name.reason = "Must contain 3 or more characters!";
		} else if (!namePattern.test(val)) {
			prem.addrInput.name.reason = "Must only contain numbers or letters!";
		}

		prem.addrInput.name.valid = valid;
	}

	prem.checkCat = function () {
		$('.tooltip').remove();
		var val = prem.addrInput.cat.val;
		var valid = false;

		if (val.length < 16 && val.length > 2 && namePattern.test(val)) {
			valid = true;
		} else if (val.length > 16) {
			prem.addrInput.cat.reason = "Must only contain 16 characters or less!";
		} else if (val.length < 3) {
			prem.addrInput.cat.reason = "Must contain 3 or more characters!";
		} else if (!namePattern.test(val)) {
			prem.addrInput.cat.reason = "Must only contain numbers or letters!";
		}

		prem.addrInput.cat.valid = valid;
	}
	
	prem.addCommas = function (name) {
		var prevVal = prem.filterInput[name].replace(/,/g, "");

		if (prevVal == "" || Number.isNaN(parseFloat(prevVal)) || (!isNaN(prevVal) && prevVal[prevVal.length - 1] == ".")) {
			return;
		}

		prem.filterInput[name] = numberWithCommas(prevVal);
	}

	prem.customGraph = function () {
		$scope.basic.isCustom = true;
		$(".collapse").one("hidden.bs.collapse", event => {
			if (!event.target.id.includes("Home")) {
				$("#Home").collapse("show");
			}
		});
		resetSideBar();
		$scope.basic.tempAddr = {
			addr: '',
			url: ''
		};
		$("#Home").collapse("show").ready(() => {
			$(".collapse").unbind("hidden.bs.collapse");
		});
	}

	prem.customOff = function () {
		$scope.basic.isCustom = false;
		prem.addrs = [];
	}

	prem.makeGraph = function () {
		if (prem.addrs.length <= 1) return;
		var url = window.location + "/group/c?addr[]=" + prem.addrs[0];
		for (var i = 1; i < prem.addrs.length; i++) {
			url += "&addr[]=" + prem.addrs[i];
		}
		$("#overlay").modal("hide");
		prem.startLoader();
		$('#iframe1').attr('src', formatFilters(prem.filterInput, url));
		prem.customOff();
	}

	function formatFilters(filters, url) {
		if (filters['minTime'].trim() === "") {
			filters = JSON.parse(JSON.stringify(dFilters));
		}

		for (let filter in filters) {

			var urlFilter = `${filter}=`;

			if (url.includes(urlFilter)) {
				if (url.includes("&" + urlFilter)) {
					urlFilter = "&" + urlFilter;
				}

				var temp = url.substring(url.indexOf(urlFilter));
				if (temp.match(/&/g).length > 1) {
					temp = temp.substring(0, temp.indexOf("&", 1));
				}

				url = url.replace(temp, "");
			}

			var val = filters[filter].toString().replace(/,/g, "");
			if (filter.toLowerCase().includes('time') && isNaN(val)) {
				val = moment(val, dateFormat).valueOf() / 1000;
				if (isNaN(val)) {
					if (filter.includes("min")) {
						val = "oldest";
					} else {
						val = "latest";
					}
				}
			}

			url += `&${filter}=${val}`;
		}

		return url.replace('?&', '?');
	}

	prem.toggle = function (addr) {
		if ($(`#${addr}`).css('color') == 'rgb(255, 255, 255)') {
			$(`#${addr}`).css("color", '#495057');
			for (var i = 0; i < prem.addrs.length; i++) {
				if (prem.addrs[i] == addr) {
					prem.addrs.splice(i, 1);
				}
			}
		} else {
			prem.addrs.push(addr);
			$(`#${addr}`).css("color", 'rgb(255, 255, 255)');
		}
	}

	var conversionToSec = {
		"second": 1,
		"minute": 60,
		"hour": 3600,
		"day": 86400,
		"week": 604800,
		"month": 2592000,
		"year": 31556952,
		"decade": 315569520
	};

	function convertToSec(amt, timeString) {
		for (let time in conversionToSec) {
			if (timeString.toLowerCase().includes(time)) {
				return amt*conversionToSec[time];
			}
		}

		return 0;
	}

	function getTimeScale(sec) {
		var times = Object.keys(conversionToSec);

		for (var i = times.length - 1; i >= 0; i--) {
			if (sec % conversionToSec[times[i]] == 0) {
				return times[i];
			}
		}

		return null;
	}

	// REVIEW TIME
	function setTime(f, time) {
		$scope.$apply(function () {
			prem.filterInput[f] = time;
		});
	}

	prem.submit = async function (type) {
		for (let filter in prem.filterInput) {
			if (moment(prem.filterInput[filter], dateFormat, true).isValid()) {
				$(`input[name='${filter}']`).val(moment(prem.filterInput[filter], dateFormat).valueOf()/1000);
			} else if (filter.includes("Time")) {
				var amt = prem.filterInput[filter].replace(/[^0-9]/g,'');

				if (amt === "") {
					amt = 1;
				}

				var ms = -convertToSec(amt, prem.filterInput[filter]);
				
				if (ms === 0) {
					ms = $(`#${filter}Ranges option:first`).val();
				}

				$(`input[name='${filter}']`).val(ms);
			} else {
				$(`input[name='${filter}']`).val(prem.filterInput[filter].toString().replace(/,/g, ""));
			}
		}

		let resp = await $scope.main.submit(type);

		if (resp.toLowerCase().includes("success")) {
			$scope.basic.updateKnown();
			$(`.modal`).modal('hide');
		}

		for (let filter in prem.filterInput) {
			$(`input[name='${filter}']`).val(numberWithCommas(prem.filterInput[filter]));
		}
	}
}

function receiveMessage(event) {
	if (event.origin == window.location.origin) {
		if (event.data.type == "add") {
			let vm = angular.element($('body')).scope();
			vm.$apply(`prem.showOverlay(${JSON.stringify(event.data)})`);
		}
	}
}

window.addEventListener("message", receiveMessage, false);