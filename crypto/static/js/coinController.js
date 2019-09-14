(function () {
	'use strict';

	angular
		.module('txs', [])
		.factory('PagerService', PagerService)
		.controller('txsController', ['PagerService', 'filterFilter', '$scope', txs])
		.directive('ngInitTime', function($parse) {
			return {
				scope: { 
					formatTime: "&callbackFn" 
				},
				link: function(scope, element, attr) {
					$(element).html(`${attr.name}: ${scope.formatTime({time: attr.unix})}`);
				}
			};
		});;

	function txs(PagerService, filter, $scope) {
		var vm = this;
		var order      = 'DESC';
		var sort 	   = 'blocktime';
		var dateFormat = "M/DD/YY h:mm A"; // REVIEW
		var tempAddrs  = [];
		$('#loadingBar').hide();
		$('#iframe').hide();
		$('#body').show();

		vm.selCollapsed = [];
		
		vm.graph;
		vm.isGraph = false;
		vm.txs = [];
		vm.pager = {};
		vm.dropText = "Most Recent";
		vm.collapseText = "Show All Transactions";
		vm.selection;

		vm.pager = PagerService.GetPager(totalTxs, 1);
		vm.minTx = minTx;
		vm.lastTx = lastTx;

		vm.currentId = 0;

		vm.savedTxs   = {};
		vm.txLoading  = false;
		vm.rowTxs	  = true;

		vm.graphFilters = JSON.parse(JSON.stringify(dFilters));
		vm.graphFilters.minTime = "";
		vm.graphFilters.maxTime = "";

		vm.dURLParams = formatFilters(vm.graphFilters, "").replace("&", "?");

		$(function () {
			$('[data-toggle="tooltip"]').tooltip({
				trigger: 'hover'
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

			if (dFilters['minTime'] != "oldest") {
				vm.graphFilters.minTime = moment.unix(dFilters['minTime']).format(dateFormat);
			} else {
				vm.graphFilters['minTime'] = "oldest";
			}
			
			if (dFilters['maxTime'] != "latest") {
				vm.graphFilters.maxTime = moment.unix(dFilters['maxTime']).format(dateFormat);
			} else {
				vm.graphFilters['maxTime'] = "latest";
			}

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

			for (let filter in vm.graphFilters) {
				if (!isNaN(vm.graphFilters[filter])) {
					vm.graphFilters[filter] = numberWithCommas(vm.graphFilters[filter]);
				}
			}
		});

		function setTime(f, time) {
			$scope.$apply(function() {
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

		vm.addCommas = function(name) {
			var prevVal = vm.graphFilters[name].replace(/,/g, "");

			if (prevVal == "" || Number.isNaN(parseFloat(prevVal)) || (!isNaN(prevVal) && prevVal[prevVal.length - 1] == ".")) {
				return;
			}

			vm.graphFilters[name] = numberWithCommas(prevVal);
		}

		vm.formatTime = function(mill) {
			return moment.unix(mill).format(dateFormat) + " " + moment.tz(moment.tz.guess()).format("z");
		}

		vm.setPage = async function(page) {
			if (vm.pager.totalPages < 1) {
				vm.pager = PagerService.GetPager(totalTxs, page);
			}
			if (page < 1 || page > vm.pager.totalPages) {
				return;
			}

			// get pager object from service
			vm.pager = PagerService.GetPager(totalTxs, page);
			$('[data-toggle="tooltip"]').tooltip('hide');

			// get current page of items
			var url = `../getTxs?page=${vm.pager.currentPage - 1}&sort=${sort}&order=${order}`;

			let isSelected  = vm.selection !== undefined;
			let isKnown 	= isSelected && isInArr(_addr, vm.selection.addr);
			let isTemp  	= isSelected && isInArr(tempAddrs, vm.selection.addr);

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
					vm.txs 		  = data;
					vm.txLoading  = false;
				});
				vm.savedTxs[reqSig] = data;
				
				$(function () {
					$('[data-toggle="tooltip"]').tooltip({
						trigger: 'hover'
					});
				});
			}
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
					val = moment(val, dateFormat).valueOf()/1000;
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
				vm.dropText = "Most Recent";
				sort = 'blocktime';
				order = 'DESC';
			} else if (propertyName == "value" && reverse) {
				vm.dropText = "Transaction Amount ↓";
				sort = 'amount';
				order = 'DESC';
			} else if (propertyName == "value" && !reverse) {
				vm.dropText = "Transaction Amount ↑";
				sort = 'amount';
				order = 'ASC';
			}
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
			var url = window.location + "";

			if (!url.includes('?')) {
				url += "?";
			}

			url = formatFilters(vm.graphFilters, url);

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
			$('#resetBtn').prop('disabled', true);
			$('#filterBtn').prop('disabled', true);
			var url = `../getGraph?`;
			$('[data-toggle="tooltip"]').tooltip('hide');
			if (_addr) {
				for (var n = 0; n < _addr.length; n++) {
					url += "&addr[]=" + _addr[n];
				}
			}
			
			url = formatFilters(vm.graphFilters, url);
			var resp = await $.get(url);

			if (resp.nodes.length == 0 && resp.edges.length == 0) {
				$('#loadingBar').hide();
				$('#graph').html('<div style="margin-top: 20%">Nothing Found.</div>');
				document.getElementById('graphContainer').style = "cursor: auto";
				$('#filterBtn').prop('disabled', false);
				$('#resetBtn').prop('disabled', false);
			} else {
				vm.graph = {
					nodes: resp.nodes,
					edges: resp.edges
				}
				totalTxs = resp.totalTxs;
				drawGraph(true, vm.graph);
			}
		}

		vm.loadedGraph = function () {
			vm.isGraph = true;
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

					if (!isCatKnown || (vm.selection && isInArr(tempAddrs, vm.selection.addr))) {
						vm.selCollapsed.push({
							sender: tx.sourceAddr,
							receiver: tx.targetAddr
						});
					}
					
					tempNum += tx.txsNum;
				}
				totalTxs = tempNum;
			}

			if (properties.edges.length > 0 || properties.nodes.length > 0) {
				vm.setPage(1);
				$(function () {
					$('[data-toggle="tooltip"]').tooltip({
						trigger: 'hover'
					});
				});
			}
		}

		function getAddrConnections(addr) {
			var distinctAddrs = [];

			var rels = data.edges.get();

			for (var i = 0; i < rels.length; i++) {
				let source   = rels[i].sourceAddr;
				let target   = rels[i].targetAddr
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

		vm.addTempGraph = async function(properties) {
			if (properties.nodes.length > 0) {
				let id = properties.nodes[0];
				let node = data.nodes.get(id);

				var addr = node.addr;

				if (!isInArr(tempAddrs, addr) && !isInArr(_addr, addr)) {
					var url = `../getGraph?`;
					url += `&addr[]=${addr}&lastId=${data.edges.get().length}`;
	
					document.getElementById('graphContainer').style = "cursor: wait";
	
					var connections = getAddrConnections(addr);
	
					for (var i = 0; i < connections.length; i++) {
						url += `&addr[]=!${connections[i]}`;
					}
				
					url = formatFilters(vm.graphFilters, url);
	
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
	
					node.title = node.title.replace("Double Click to Load Transactions! (May Lag Site!)", "");
					data.nodes.update(node);
	
					vm.graph = {
						nodes: data.nodes.get(),
						edges: data.edges.get()
					}
					
					tempAddrs.push(addr);
	
					network.selectEdges([]);
					network.selectNodes([]);
	
					onDeselectNodes();
					onDeselectEdges();
	
					setTimeout(function() {
						stopPhysics(vm.graph);
					}, 1000);
				}
			}
		}

		vm.startLoader = function() { 
			$('body').html('<div style="min-height: 100vh; display: flex; align-items: center;"><div class="spinner-grow mx-auto" style="width: 15rem; height: 15rem;" role="status"><span class="sr-only">Loading...</span></div></div>');
		}

		if (totalTxs < 500) {
			vm.loadGraph();
		}
		

		vm.setPage(1);

		setInterval(function () {
			vm.savedTxs = {};
		}, 300000);

		$(window).resize(function() {
			if ($(window).width() < 1000 && vm.rowTxs) {
				$scope.$apply(() => {
					vm.rowTxs = false;
				});
			} else if ($(window).width() > 1000 && !vm.rowTxs) {
				$scope.$apply(() => {
					vm.rowTxs = true;
				});
			}
		});
	}

	function PagerService() {
		// service definition
		var service = {};

		service.GetPager = GetPager;

		return service;

		// service implementation
		function GetPager(totalItems, currentPage, pageSize) {
			// default to first page
			currentPage = currentPage || 1;

			// default page size is 10
			pageSize = pageSize || 10;

			// calculate total pages
			var totalPages = Math.ceil(totalItems / pageSize);

			var startPage, endPage;
			if (totalPages <= 10) {
				// less than 10 total pages so show all
				startPage = 1;
				endPage = totalPages;
			} else {
				// more than 10 total pages so calculate start and end pages
				if (currentPage <= 6) {
					startPage = 1;
					endPage = 10;
				} else if (currentPage + 4 >= totalPages) {
					startPage = totalPages - 9;
					endPage = totalPages;
				} else {
					startPage = currentPage - 5;
					endPage = currentPage + 4;
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
})();