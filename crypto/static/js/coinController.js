var main = angular
	.module('txs', [])
	.factory('PagerService', PagerService)
	.controller('txsController', ['PagerService', '$scope', txs])
	.directive('ngInitTime', function ($parse) {
		return {
			scope: {
				formatTime: "&callbackFn"
			},
			link: function (scope, element, attr) {
				$(element).text(`${attr.name}: ${scope.formatTime({time: attr.unix})}`);
			}
		};
	}).directive('ngOverflow', ['$parse', '$rootScope', '$exceptionHandler', function ($parse, $rootScope, $exceptionHandler) {
		return {
			restrict: 'A',
			scope: {
				if: "@ngOverflow",
				else: "@ngNotOverflow"
			},
			compile: function ($element, attrs) {
				return function ngEventHandler(scope, el) {
					function checkOverflow() {
						var totalWidth = 0;
						$(el).find("*").each(function() {
							if ($(this).children().length == 0) {
								totalWidth += $(this).outerWidth();
							}
						});
						//$(el).outerWidth() > $(el).parent().innerWidth() || $(el).outerHeight() > $(el).parent().innerHeight()
						//console.log($(el).width() - totalWidth);
						if ($(el).width() - totalWidth < 20) {
							scope.$parent.$evalAsync(scope.if);
						} else if ($(el).width() - totalWidth*2 > 0) {
							scope.$parent.$evalAsync(scope.else);
						}
					}
					checkOverflow();
					
					$(window).resize(checkOverflow);
				};
			}
		};
	}]);

$.event.special.widthChanged = {
	remove: function () {
		$(this).children('iframe.width-changed').remove();
	},
	add: function () {
		var elm = $(this);
		var iframe = elm.children('iframe.width-changed');
		if (!iframe.length) {
			iframe = $('<iframe/>').addClass('width-changed').prependTo(this);
		}
		var oldWidth = elm.width();

		function elmResized() {
			var width = elm.width();
			if (oldWidth != width) {
				elm.trigger('widthChanged', [width, oldWidth]);
				oldWidth = width;
			}
		}

		var timer = 0;
		var ielm = iframe[0];
		(ielm.contentWindow || ielm).onresize = function () {
			clearTimeout(timer);
			timer = setTimeout(elmResized, 20);
		};
	}
}

function txs(PagerService, $scope) {
	var vm = this;

	var order = 'DESC';
	var sort = 'blocktime';
	vm.txs = [];
	vm.pager = {};
	//vm.dropText = "Most Recent";
	vm.pager = PagerService.GetPager(totalTxs, 1);

	var pageCnt = 10;
	var tempTotalTxs = totalTxs;
	vm.tempAddrs = [];

	$('#loadingBar').hide();
	vm.selCollapsed = [];
	vm.graph;
	vm.isGraph = false;
	vm.selection;

	vm.currentId = 0;

	vm.savedTxs = {};
	vm.txLoading = true;
	vm.rowTxs = true;
	vm.txGraph = false;

	vm.graphFilters = JSON.parse(JSON.stringify(dFilters));
	vm.graphFilters.minTime = "";
	vm.graphFilters.maxTime = "";

	$(function () {
		$('[data-toggle="tooltip"]').tooltip({
			trigger: 'hover',
			boundary: "window"
		});
	});
	$(function () {
		$('input[name="minTime"]').daterangepicker({
			singleDatePicker: true,
			timePicker: true,
			showDropdowns: true,
			autoUpdateInput: false,
			parentEl: "#time .dropdown-menu",
			minDate: moment.unix(lastTx).format(dateFormat),
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
			parentEl: "#time .dropdown-menu",
			minDate: moment.unix(lastTx).format(dateFormat),
			locale: {
				format: dateFormat,
				cancelLabel: 'Clear'
			}
		});

		if (dFilters.minTime != "oldest") {
			vm.graphFilters.minTime = moment.unix(dFilters['minTime']).format(dateFormat);
		} else {
			vm.graphFilters.minTime = "oldest";
		}

		if (dFilters.maxTime != "latest") {
			vm.graphFilters.maxTime = moment.unix(dFilters['maxTime']).format(dateFormat);
		} else {
			vm.graphFilters.maxTime = "latest";
		}

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

		for (let filter in vm.graphFilters) {
			if (!filter.includes("Time") && !isNaN(vm.graphFilters[filter])) {
				vm.graphFilters[filter] = numberWithCommas(vm.graphFilters[filter]);
			}
		}

		vm.dURLParams = formatFilters(vm.graphFilters, "").replace("&", "?");

		vm.setPage(1);
	});

	function setTime(f, time) {
		$scope.$apply(function () {
			vm.graphFilters[f] = time;
		});

		$("#time").attr("data-lastEdit", f);
	}

	function isInArr(arr, val) {
		if (arr) {
			for (var i = 0; i < arr.length; i++) {
				if (arr[i] == val) {
					return true;
				}
			}
		}

		return false;
	}

	vm.resetTotalTxs = function () {
		tempTotalTxs = totalTxs;
	}

	vm.addCommas = function (name) {
		var prevVal = vm.graphFilters[name].replace(/,/g, "");

		if (prevVal == "" || Number.isNaN(parseFloat(prevVal)) || (!isNaN(prevVal) && prevVal[prevVal.length - 1] == ".")) {
			return;
		}

		vm.graphFilters[name] = numberWithCommas(prevVal);
	}

	vm.formatTime = function (mill) {
		return moment.unix(mill).format(dateFormat) + " " + moment.tz(moment.tz.guess()).format("z");
	}

	vm.setPage = async function (page) {
		if (vm.pager.totalPages < 1) {
			vm.pager = PagerService.GetPager(tempTotalTxs, page, pageCnt);
		}
		if (page < 1 || page > vm.pager.totalPages) {
			return; // change
		}

		// get pager object from service
		vm.pager = PagerService.GetPager(tempTotalTxs, page, pageCnt);
		$('[data-toggle="tooltip"]').tooltip('hide');

		// get current page of items
		var url = `../getTxs?page=${vm.pager.currentPage - 1}&sort=${sort}&order=${order}`;

		let isSelected = vm.selection !== undefined;
		let isKnown = isSelected && isInArr(_addr, vm.selection.addr);
		let isTemp = isSelected && isInArr(vm.tempAddrs, vm.selection.addr);

		if (isKnown || isTemp) {
			url += `&addr[]=${vm.selection.addr}`;
		} else if (vm.selCollapsed.length > 0) {
			for (var i = 0; i < vm.selCollapsed.length; i++) {
				url += `&sender[]=${vm.selCollapsed[i].sender}&receiver[]=${vm.selCollapsed[i].receiver}`;
			}
		} else if (_addr) {
			for (var n = 0; n < _addr.length; n++) {
				url += "&addr[]=" + _addr[n];
			}
			/*
			if (vm.tempAddrs.length > 0) {
				for (var n = 0; n < vm.tempAddrs.length; n++) {
					url += "&addr[]=" + vm.tempAddrs[n];
				}
			}
			*/
		}

		var reqSig = url;
		var txSave = vm.savedTxs[reqSig] || undefined;

		if (txSave) {
			vm.txs = txSave;
		} else {
			vm.txLoading = true;

			url = formatFilters(vm.graphFilters, url);

			var data = await $.get(url);

			$scope.$apply(() => {
				vm.txs = data;
				vm.txLoading = false;
			});
			vm.savedTxs[reqSig] = data;
		}

		$(function () {
			$('[data-toggle="tooltip"]').tooltip({
				trigger: 'hover',
				boundary: "window"
			});

			$("a.addr").click(function () {
				vm.startLoader();
				parent.postMessage({
					type: 'crumb',
					crumb: {
						link: $(this).attr("href"),
						name: $(this).text().trim()
					}
				}, window.location.origin);
			});
		});
	}

	function formatFilters(filters, url) {
		/*
		if (filters['minTime'].trim() === "") {
			filters = JSON.parse(JSON.stringify(dFilters));
		}
		*/

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
			if (filter.includes('Time') && isNaN(val)) {

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

	vm.sortBy = function (propertyName, reverse) {
		if (propertyName == "time") {
			//vm.dropText = "Most Recent";
			sort = 'blocktime';
			order = 'DESC';
		} else if (propertyName == "value" && reverse) {
			//vm.dropText = "Transaction Amount ↓";
			sort = 'amount';
			order = 'DESC';
		} else if (propertyName == "value" && !reverse) {
			//vm.dropText = "Transaction Amount ↑";
			sort = 'amount';
			order = 'ASC';
		}
		$("#txSort .dropdown-item").removeClass("active");
		$("#" + sort + order).addClass("active");
		vm.setPage(vm.pager.currentPage);
	}

	vm.rangeBy = function (fieldName, minValue, maxValue) {
		if (minValue === undefined) minValue = 0;
		if (maxValue === undefined) maxValue = Number.MAX_VALUE;

		return function predicateFunc(item) {
			return minValue <= item[fieldName] && item[fieldName] <= maxValue;
		};
	}

	vm.setFilters = function () {
		var name = $("#name").text().trim();
		vm.startLoader();
		var url = window.location + "";

		if (!url.includes('?')) {
			url += "?";
		}

		url = formatFilters(vm.graphFilters, url);

		parent.postMessage({
			type: 'crumb',
			crumb: {
				link: url,
				name: name
			}
		}, window.location.origin);

		window.location = url;
	}

	vm.removeFilter = function (event) {
		var el = event.target;
		if (!$(el).is("button")) {
			el = $(el).parent();
		}
		vm.graphFilters[$(el).attr("name")] = $(el).attr("data-value");
		$(`input[name='${$(el).attr("name")}']`).addClass("filterChange");
		$(el).fadeOut();
	}

	vm.loadGraph = async function () {
		document.getElementById('graphContainer').style = "cursor: wait";
		$('#text').text('0%')
		$('#bar').css('width', '20px');
		$('loadingBar').css('opacity', 1);
		$('#loadingBar').show();
		$('#filterBtn').prop('disabled', true);
		vm.isGraph = true;
		var url = `../getGraph?`;
		$('[data-toggle="tooltip"]').tooltip('hide');
		if (_addr) {
			for (var n = 0; n < _addr.length; n++) {
				url += "&addr[]=" + _addr[n];
			}
		}

		url = formatFilters(dFilters, url);
		var resp = await $.get(url);

		if (resp.nodes.length == 0 && resp.edges.length == 0) {
			$('#loadingBar').hide();
			$('#graph').html('<div style="margin-top: 20%">Nothing Found.</div>');
			document.getElementById('graphContainer').style = "cursor: auto";
			$('#filterBtn').prop('disabled', false);
		} else {
			vm.graph = {
				nodes: resp.nodes,
				edges: resp.edges
			}
			//totalTxs = resp.totalTxs;
			drawGraph(true, vm.graph);
		}
	}

	vm.highlight = function (id, isNode) {
		if (!vm.graph) return;

		if (isNode) {
			network.selectNodes([id], false);
			network.focus(id, {
				scale: 1,
				animation: true
			});
			return;
		}
		let source = id.source;
		let target = id.target;
		var edgeId;

		for (var i = 0; i < vm.graph.edges.length; i++) {
			if (vm.graph.edges[i].source == source && vm.graph.edges[i].target == target) {
				edgeId = vm.graph.edges[i].id
				break;
			}
		}

		if (edgeId) {
			network.fit({
				animation: true
			});
			network.selectEdges([edgeId]);
		}
	}

	// REVIEW
	vm.select = function (properties) {
		var isCatKnown = false;
		var node;
		if (properties.nodes.length > 0) {
			let id = properties.nodes[0];
			node = data.nodes.get(id);
			isCatKnown = isInArr(_addr, node.addr);
			if (isCatKnown && _addr.length == 1) {
				return; // review
			}
			vm.selection = node;
		}

		if (properties.edges.length > 0) {
			var tempTxs = properties.edges
			var tempNum = 0;
			for (var i = 0; i < tempTxs.length; i++) {
				let tx = data.edges.get(tempTxs[i]);

				if (!isCatKnown || (vm.selection && isInArr(vm.tempAddrs, vm.selection.addr))) {
					vm.selCollapsed.push({
						sender: tx.sourceAddr,
						receiver: tx.targetAddr
					});
				}

				tempNum += tx.txsNum;
			}
			tempTotalTxs = tempNum;
		}

		if (properties.edges.length > 0 || properties.nodes.length > 0) {
			vm.setPage(1);
		}
	}

	function getAddrConnections(addr) {
		var distinctAddrs = [];

		var rels = data.edges.get();

		for (var i = 0; i < rels.length; i++) {
			let source = rels[i].sourceAddr;
			let target = rels[i].targetAddr
			let isSource = target === addr && !isInArr(distinctAddrs, source);
			let isTarget = source === addr && !isInArr(distinctAddrs, target);

			if (isSource) {
				distinctAddrs.push(source);
			} else if (isTarget) {
				distinctAddrs.push(target);
			}
		}

		return distinctAddrs;
	}

	vm.addTempGraph = async function (properties) {
		if (properties.nodes.length > 0) {
			let id = properties.nodes[0];
			let node = data.nodes.get(id);

			var addr = node.addr;

			if (!isInArr(vm.tempAddrs, addr) && !isInArr(_addr, addr)) {
				var url = `../getGraph?`;
				url += `&addr[]=${addr}&lastId=${data.edges.get().length}`;

				document.getElementById('graphContainer').style = "cursor: wait";

				var connections = getAddrConnections(addr);

				for (var i = 0; i < connections.length; i++) {
					url += `&addr[]=!${connections[i]}`;
				}

				url = formatFilters(dFilters, url);

				var resp = await $.get(url);

				network.setOptions({
					"physics": {
						"enabled": true
					}
				});

				var tempNodes = resp.nodes;

				for (var i = tempNodes.length - 1; i > -1; i--) {
					if (data.nodes.get(tempNodes[i].id) !== null) {
						tempNodes.splice(i, 1);
					}
				}

				data.nodes.add(tempNodes);
				data.edges.add(resp.edges);

				node.title = node.title.replace("Double Click to Load Transactions!", "");

				data.nodes.update(node);

				vm.graph = {
					nodes: data.nodes.get(),
					edges: data.edges.get()
				}

				vm.tempAddrs.push(addr);

				network.selectEdges([]);
				network.selectNodes([]);

				onDeselectNodes();
				onDeselectEdges();

				setTimeout(function () {
					stopPhysics(vm.graph);
					$(function () {
						$('[data-toggle="tooltip"]').tooltip({
							trigger: 'hover',
							boundary: "window"
						});
					});
				}, 1000);
			}
		}
	}

	vm.openAsCustom = function () {
		var url = "../group/c" + vm.dURLParams;

		for (var i = 0; i < _addr.length; i++) {
			url += "&addr[]=" + _addr[i];
		}

		for (var i = 0; i < vm.tempAddrs.length; i++) {
			url += "&addr[]=" + vm.tempAddrs[i];
		}

		window.location = url;
	}

	vm.startLoader = function () {
		$('body').html('<div style="min-height: 100vh; display: flex; align-items: center;"><div class="spinner-grow mx-auto" style="width: 15rem; height: 15rem;" role="status"><span class="sr-only">Loading...</span></div></div>');
	}

	if (totalTxs < 500) {
		vm.loadGraph();
	}

	setInterval(function () {
		vm.savedTxs = {};
	}, 300000);

	function onTxWidthChange() {
		if ($("#txListContainer").width() < 900 && vm.rowTxs) {
			$scope.$apply(function() {
				vm.rowTxs = false;
				pageCnt = 5;
				vm.pager = PagerService.GetPager(vm.pager.totalItems, vm.pager.currentPage, pageCnt);
			});
		} else if ($("#txListContainer").width() > 900 && !vm.rowTxs) {
			$scope.$apply(function() {
				vm.rowTxs = true;
				pageCnt = 10;
				vm.pager = PagerService.GetPager(vm.pager.totalItems, vm.pager.currentPage, pageCnt);
			});
		}

		if (vm.txGraph) {
			$("#txListContainer").css("height", $("#graph").height() - $("#txTop").height()*2);
		} else {
			$("#txListContainer").css("height", "auto");
		}
	}

	$(function () {
		$(window).resize(function () {
			if (vm.isGraph) {
				$("#graph").resizable({
					maxWidth: $("#graphContainer").innerWidth() * 0.95,
					minWidth: $("#graphContainer").innerWidth() * 0.40
				});
			}
		});

		onTxWidthChange();
		$("#txListContainer").on("widthChanged", onTxWidthChange);

		$("#graph").resize(function () {
			var width = 100 * $("#graph").outerWidth() / $("#graphContainer").innerWidth();

			$("#graph").css("width", width + "%");
			$("#graphContainer").css("height", 100 * $("#graph").outerHeight() / $("#body").innerHeight() + "%");

			if (width - 45 < 1) {
				$("#txContainer").css("width", 100 - (width + 2.5) + "%");
				$("#txListContainer").css("height", $("#graph").height() - $("#txTop").height()*2);
				if (!vm.txGraph) {
					$("#txContainer").appendTo("#graphContainer").on("widthChanged", onTxWidthChange);
					$scope.$apply(() => {
						vm.txGraph = true;
					});
					onTxWidthChange();
				}
				$('[data-toggle="tooltip"]').tooltip({
					trigger: 'hover',
					boundary: "window"
				});
			} else if (width - 45 > 1 && vm.txGraph) {
				$scope.$apply(() => {
					vm.txGraph = false;
				});
				$("#txListContainer").css("height", "auto");
				$("#txContainer").appendTo("#body").css("width", "auto").on("widthChanged", onTxWidthChange);
				onTxWidthChange();
				$('[data-toggle="tooltip"]').tooltip({
					trigger: 'hover',
					boundary: "window"
				});
				//$("#txCounter").prependTo("#txTop");
			}
		});
	});
}

function PagerService() {
	// service definition
	var service = {};

	service.GetPager = GetPager;

	return service;

	// service implementation
	function GetPager(totalItems, currentPage, pageCnt, pageSize) {
		// default to first page
		currentPage = currentPage || 1;

		// default page size is 10
		pageSize = pageSize || 10;

		// default page count (# of page #s to be able to click) is 10
		pageCnt = pageCnt || 10;

		// calculate total pages
		var totalPages = Math.ceil(totalItems / pageSize);

		var startPage, endPage;
		if (totalPages <= pageCnt) {
			// less than pageCnt total pages so show all
			startPage = 1;
			endPage = totalPages;
		} else {
			offset = Math.floor(pageCnt / 2) + 1;
			// more than 10 total pages so calculate start and end pages
			if (currentPage <= offset) {
				startPage = 1;
				endPage = pageCnt;
			} else if (currentPage + (pageCnt - offset) >= totalPages) {
				startPage = totalPages - (pageCnt - 1);
				endPage = totalPages;
			} else {
				startPage = currentPage - Math.floor(pageCnt / 2);
				endPage = currentPage + (pageCnt - offset);
			}
		}

		// calculate start and end item indexes
		var startIndex = (currentPage - 1) * pageSize;
		var endIndex = Math.min(startIndex + pageSize - 1, totalItems - 1);

		// create an array of pages to ng-repeat in the pager control
		var pages = _.range(startPage, endPage + 1);

		// return object with all pager properties required by the view
		return {
			totalItems: totalItems,
			currentPage: currentPage,
			pageSize: pageSize,
			totalPages: totalPages,
			startPage: startPage,
			endPage: endPage,
			startIndex: startIndex,
			endIndex: endIndex,
			pages: pages
		};
	}
}