self.addEventListener("fetch", event => {
    const url = new URL(event.request.url);

    if (url.href === "https://totaljerkface.com/get_level.hw") {
      event.respondWith(fetch("get_level.hw"));
    }
  });
(function() {
    const OriginalXHR = window.XMLHttpRequest;
    window.XMLHttpRequest = function() {
        const xhr = new OriginalXHR();
        let method;
        let url;
        const originalOpen = xhr.open;
        xhr.open = function(m, u, ...args) {
            method = m;
            url = u;

            return originalOpen.call(xhr, m, u, ...args);
        };
        const originalSend = xhr.send;
        xhr.send = function(body) {
            if (url.includes("get_level.hw")) {
                const params = new URLSearchParams(body);
                const action = params.get("action");
                const uploaded = params.get("uploaded");
                const sortby = params.get("sortby")
                let file;
                if (action === "get_featured") {
                    file = "xml/featured.xml";
                }
                if (action === "get_all") {

                    file =
                    `xml/${sortby}/${uploaded}/page${params.get("page")}.xml`;

                }
                if (file) {

                    fetch(file)
                    .then(r => r.text())
                    .then(text => {

                        Object.defineProperty(xhr, "readyState", {
                            value: 4
                        });

                        Object.defineProperty(xhr, "status", {
                            value: 200
                        });

                        Object.defineProperty(xhr, "responseText", {
                            value: text
                        });

                        Object.defineProperty(xhr, "response", {
                            value: text
                        });

                        xhr.dispatchEvent(new Event("readystatechange"));
                        xhr.dispatchEvent(new Event("load"));
                        xhr.dispatchEvent(new Event("loadend"));

                        if (typeof xhr.onreadystatechange === "function") {
                            xhr.onreadystatechange();
                        }

                        if (typeof xhr.onload === "function") {
                            xhr.onload();
                        }

                    });
                    return;
                }

            }


            return originalSend.call(xhr, body);
        };


        return xhr;

    };

})();
