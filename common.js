	function changed(x)
	{
		// sect108.htm
		// make svg view element node108
		var a = x.href.split("/")
		var name = a[a.length-1]
		if(name.startsWith("sect") && name.endsWith(".htm"))
		{
			var page = name.substr(4,name.length-4-4)
			var target = "node" + page
			console.log("move to ",target)
			var w = document.getElementById("gframe").contentWindow
			var svg = w.document
			var node = svg.getElementById(target)
			var view = node.farthestViewportElement
			var g = view.getAttribute("viewBox").split(" ")
	        console.log(g)

	        // getBBox is defined in the SVG specification it returns coordinates in the local coordinate system after the application of transforms.
	        // 
			var bbox = node.getBoundingClientRect ()
			console.log(bbox)
	        console.log(bbox.x,"x",w.scrollX,"y",w.scrollY)
			w.scrollTo(w.pageXOffset+bbox.x-w.innerWidth/2,w.pageYOffset+bbox.y-bbox.height) // top center
			//var t = view.setAttribute("viewBox",g.join(" "))
		}
	}