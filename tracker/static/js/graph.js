var clipboard = new ClipboardJS('.btn');

clipboard.on('success', function (e) {
	e.action
	e.clearSelection();
});

clipboard.on('error', function (e) {
	console.error('Action:', e.action);
	console.error('Trigger:', e.trigger);
});

function fullGraph() {
	document.getElementById('graph').requestFullscreen();
}

function toggleDarkMode() {
	console.log($('#graph').css('background-color'));
	if ($('#graph').css('background-color') == "rgb(0, 0, 0)") {
		$('#graph').css('background-color', 'white');
		network.setOptions({
			"nodes": {
				"font": {
					"color": "#000000"
				}
			}
		});
	} else {
		$('#graph').css('background-color', 'black');
		network.setOptions({
			"nodes": {
				"font": {
					"color": "#ffffff"
				}
			}
		});
	}
}

// This method is responsible for drawing the graph, returns the drawn network
function drawGraph(stop) {
	var container = document.getElementById('graph');
	container.style = "cursor: wait";

	// adding nodes and edges to the graph
	data = {
		nodes: new vis.DataSet(nodes),
		edges: new vis.DataSet(edges)
	};

	let vm = angular.element($('body')).scope();

	var options = {
		"nodes": {
			"scaling": {
				"min": 25,
				"max": 200
			},
			"shape": "dot",
			"borderWidthSelected": 1,
			"font": {
				"color": "#000000"
			},
			"color": {
				"highlight": {
					"border": "#1f8766",
					"background": "#e5ff00"
				}
			}
		},
		"edges": {
			"arrows": {
				"to": {
					"enabled": true
				}
			},
			"scaling": {
				"min": 1,
				"max": 25
			},
			"arrowStrikethrough": false,
			"color": {
				"highlight": "#e5ff00",
				"hover": "#0062ff"
			},
			"smooth": {
				"type": "dynamic",
				"forceDirection": "none"
			},
			"font": {
				"color": "#000000"
			}
		},
		"groups": {
			"useDefaultGroups": true,
			"usdt": {
				"color": {
					"background": "#26A17B",
					"border": "#1f8766",
				}
			}
		},
		"interaction": {
			"dragNodes": true,
			"hideEdgesOnDrag": false,
			"hideNodesOnDrag": false,
			"hover": true,
			"tooltipDelay": 100,
			"hoverConnectedEdges": ("{{search.label}}" == 'All Addresses')
		},
		"layout": {
			"improvedLayout": false
		},
		"physics": {
			'stabilization': {
				'enabled': true,
				'iterations': 1000,
				'updateInterval': 100
			},
			"repulsion": {
				"nodeDistance": 400,
				"springLength": 300
			},
			"forceAtlas2Based": {
				"avoidOverlap": 0.75
			},
			"enabled": true,
			"solver": (!("{{search.label}}").includes('Addresses') && ($('#hide').text().toLowerCase().includes('collapse') || $('#maxTxsNum').attr('max') == 1)) ? "repulsion" : "forceAtlas2Based"
		}
	};
	network = new vis.Network(container, data, options);

	if (stop) {
		stopPhysics();
	}

	network.on('click', properties => {
		vm.$apply(`vm.select(${JSON.stringify(properties)})`);
	});

	network.on('deselectEdge', properties => {
		vm.$apply('vm.setTxs()');
	});

	network.on('deselectNode', properties => {
		vm.$apply('vm.setTxs()');
	});
	return network;
}

//drawGraph();

function stopPhysics() {
	setTimeout(function () {
		network.setOptions({
			"physics": {
				"enabled": false
			}
		});
		network.fit({
			animation: true
		});
		document.getElementById('graph').style = "cursor: auto";
	}, edges.length * 10);
}