function waitForLoaded (){
	let repoList = document.getElementById('assignment-repo-list')
	let spinners = repoList.getElementsByClassName('spinner')
	if ( spinners.length > 0 ){
		console.log("There are still "+ spinners.length + " spinners left")
		return
	}
	clearInterval(wait)
	afterLoaded()
}
function afterLoaded(){
	let siteContent = document.body
	let node = document.createElement('div')
	node.setAttribute("id","chrome-extension-classroom-waiter-loaded")
	node.innerHTML = "chrome-extension-classroom-waiter-loaded"
	siteContent.appendChild(node)
	console.log("loaded")
}

var wait = setInterval(waitForLoaded, 100) 