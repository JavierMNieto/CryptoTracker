var main = angular
	.module('main', [])
	.controller('mainController', ['$scope', mainController]);

function mainController($scope) {
	vm = this;
	vm.isCustom = false;
	vm.toggleBar = true;
	vm.ut = moment().utc().format('H:mm:ss');
	vm.hk = moment().tz('Asia/Hong_Kong').format('H:mm:ss');
	vm.addrs = []

	vm.formState = "";
	vm.overlay   = {};
	vm.addrInput = {
		'addr': {
			'val': '',
			'state': 'invalid'
		},
		'name': {
			'val': '',
			'state': 'invalid'
		}
	};

	vm.tempAddr = {
		addr: '',
		url: ''
	};

	vm.customGraph = function () {
		vm.isCustom = true;
		$('#searchBar').val('');
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
		var url = "{{homeUrl}}".replace(/0/, JSON.stringify(vm.addrs))
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
		vm.overlay = obj;

		if (obj.type == "edit") {
			vm.addrInput.name.val = obj.name;
		}
	}

	setInterval(function () {
		$scope.$apply(function () {
			vm.ut = moment().utc().format('H:mm:ss');
			vm.hk = moment().tz('Asia/Hong_Kong').format('H:mm:ss');
		});
	}, 1000);

	vm.submit = async function (type) {
		vm.formState = "load";

		let resp = await $.ajax({
			url: $(`#${type}`).attr('action'),
			type: 'POST',
			data: $(`#${type}`).serialize()
		});

		vm.formState = "";

		$(`.modal`).modal('hide');

		console.log(resp);

		// DO SOMETHING ON SUCCESS
	}

	vm.checkAddr = async function () {
		var val = vm.addrInput.addr.val;

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
					vm.addrInput.addr.state = "valid";
					return;
				}
			}
		}

		vm.addrInput.addr.state = "invalid";
	}

	vm.checkName = function () {
		var val = vm.addrInput.name.val;

		if (val.length < 16 && namePattern.test(val)) {

			vm.addrInput.name.state = "load";

			var addrs = $(".addr");
			var exists = false;
			var i = 0;

			while (i < addrs.length && !exists) {
				if ($(addrs[i]).text().trim().toLowerCase() == val.toLowerCase()) {
					exists = true;
				}

				i++;
			}

			if (!exists) {
				vm.addrInput.name.state = "valid";
				return;
			}
		}

		vm.addrInput.name.state = "invalid";
	}
}