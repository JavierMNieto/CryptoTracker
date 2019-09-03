(function () {
	'use strict';

	angular
		.module('txs', [])
		.factory('PagerService', PagerService)
		.controller('txsController', ['PagerService', 'filterFilter', '$scope', txs]);

	function txs(PagerService, filter, $scope) {
		var vm = this;
		var order = 'DESC';
		var sort = 'epoch';
		$('#loadingBar').hide();
		$('#iframe').hide();
		$('#body').show();

		vm.selCollapsed = [];
		
		vm.graph;
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

		vm.graphFilters = dFilters;

		vm.graphFilters.minTime = moment.unix(lastTx).format('M/DD/YY hh:mm A');
		vm.graphFilters.maxTime = moment.unix(moment().unix()).format('M/DD/YY hh:mm A');
		
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
				parentEl: "#time .dropdown-menu",
				minDate: moment.unix(lastTx).format('M/DD/YY hh:mm A'),
				maxDate: moment.unix(moment().unix()).format('M/DD/YY hh:mm A'),
				locale: {
					format: 'M/DD/YY hh:mm A'
				}
			});
			$('input[name="maxTime"]').daterangepicker({
				singleDatePicker: true,
				timePicker: true,
				showDropdowns: true,
				parentEl: "#time .dropdown-menu",
				minDate: moment.unix(lastTx).format('M/DD/YY hh:mm A'),
				maxDate: moment.unix(moment().unix()).format('M/DD/YY hh:mm A'),
				locale: {
					format: 'M/DD/YY hh:mm A'
				}
			});
		});

		vm.setPage = function setPage(page) {
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

			if (_addr !== 0 && vm.selection !== undefined && vm.selection.title.includes('Name:')) {
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
				for (let filter in vm.graphFilters) {
					var val = vm.graphFilters[filter];
					if (filter.toLowerCase().includes('time')) {
						val = moment(val, 'M/DD/YY hh:mm A').valueOf()/1000;
					}
					url += `&${filter}=${val}`;
				}

				$.get(url, data => {
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
				});
			}
		}

		vm.sortBy = function (propertyName, reverse) {
			if (propertyName == "time") {
				vm.dropText = "Most Recent";
				sort = 'epoch';
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

			for (let filter in vm.graphFilters) {
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

				var val = vm.graphFilters[filter];
				if (filter.toLowerCase().includes('time')) {
					val = moment(val, 'M/DD/YY hh:mm A').valueOf()/1000;
				}

				url += `&${filter}=${val}`;
			}

			url = url.replace("?&", "?");

			window.location = url;
		}

		vm.loadGraph = function () {
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
			for (let filter in dFilters) {
				var val = dFilters[filter]
				if (filter.toLowerCase().includes('time')) {
					val = moment(val, 'M/DD/YY hh:mm A').valueOf()/1000;
				}
				url += `&${filter}=${val}`;
			}
			url = url.replace('?&', '?');
			$.get(url, resp => {
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
			});
			
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

		vm.select = function (properties) {
			var isCatKnown = false;
			if (properties.nodes.length > 0) {
				let id = properties.nodes[0];
				let node = data.nodes.get(id);
				if (_addr.length == 1 && _addr[0] == node.addr) {
					return;
				}
				vm.selection = node;
				for (var i = 0; i < _addr.length; i++) {
					if (_addr[i] == vm.selection.addr) {
						isCatKnown = true;
						break;
					}
				}
			} 
			if (properties.edges.length > 0) {
				var tempTxs = properties.edges
				var tempNum = 0;
				for (var i = 0; i < tempTxs.length; i++) {
					let tx = data.edges.get(tempTxs[i]);

					if (!isCatKnown) {
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

		vm.startLoader = function() { 
			$('body').html('<div style="min-height: 100vh; display: flex; align-items: center;"><div class="spinner-grow mx-auto" style="width: 15rem; height: 15rem;" role="status"><span class="sr-only">Loading...</span></div></div>');
		}

		if (totalTxs < 2000) {
			vm.loadGraph();
		}

		vm.setPage(1);

		setInterval(function () {
			vm.savedTxs = {};
		}, 300000);
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