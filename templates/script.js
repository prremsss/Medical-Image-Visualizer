 const canvas = document.getElementById("canvas");
    const context = canvas.getContext("2d");
    const sliceSlider = document.getElementById('slice-slider');
    const playbutton = document.getElementById("play");
        const plus = document.getElementById("plus");
    const minus = document.getElementById("minus");

    let currentImageIndex = 0;
    let pixelData = new Uint8ClampedArray();
    let width;
    let height;
    const standarWidth = 700;
    const standarHeight = 700;
    let finalArray = [];
    let numSlices;
    let pixelData2;
    var removeEventListeners;
    const sliderText = document.getElementById("slider-text")

    fetch('/pixeldata')
        .then(res => res.json())
        .then(data => {
            handlePixelData(data);
        })
        .catch(error => {
            // Handle any errors
        });

    function handlePixelData(data) {
        pixelData = new Uint8ClampedArray(data.pixels);
        pixelData2 = JSON.parse(data.pixels);
        width = data.width;
        height = data.height;
        numSlices = pixelData2.length;
        sliderText.textContent = `${currentImageIndex}/${numSlices}`;
        const numRows = pixelData2[0].length;
        const numCols = pixelData2[0][0].length;

        // Print the shape
        console.log("Number of slices:", numSlices);
        console.log("Number of rows:", numRows);
        console.log("Number of columns:", numCols);

        grayToRGB();
        displayImage(currentImageIndex);

        console.log("before");
        console.log(width);
        sliceSlider.min = 0;
        sliceSlider.max = numSlices - 1;
        sliceSlider.value = currentImageIndex;

        // Attach scroll wheel event listener to the canvas
        canvas.addEventListener("wheel", (event) => {
            event.preventDefault();

            // Determine the scroll direction (up or down)
            const scrollDirection = event.deltaY > 0 ? "down" : "up";

            // Update the current image index based on the scroll direction
            if (scrollDirection === "up" && currentImageIndex !== 0) {
                currentImageIndex--;
                if (currentImageIndex <= 0) {
                    currentImageIndex = numSlices - 1;
                }
            } else {
                currentImageIndex++;
                if (currentImageIndex >= numSlices) {
                    currentImageIndex = 0;
                }
            }

            // Display the image at the new index
            displayImage(currentImageIndex);
            updateSliceSlider();
        });

        let intervalId = null;
        let delay = 100; // Initial delay between each image (1 second in this example)

        canvas.addEventListener('click', function (event) {
            if (intervalId === null) {
                intervalId = setInterval(displayNextImage, delay);
            } else {
                clearInterval(intervalId);
                intervalId = null;
            }
        });

        const classesToAdd =['fa','fa-play-circle-o']
        const classesToRemove=['fa','fa-pause-circle-o']
        playbutton.addEventListener('click',function (event){
            if (intervalId === null) {
                intervalId = setInterval(displayNextImage, delay);
                playbutton.classList.remove('fa-play-circle-o');
                playbutton.classList.add('fa-pause-circle-o');
            } else {
                clearInterval(intervalId);
                intervalId = null;
                 playbutton.classList.remove('fa-pause-circle-o');
    playbutton.classList.add('fa-play-circle-o');
            }
        });

        minus.addEventListener('click',function (event){
            delay += 5;
            if (intervalId !== null) {
                    clearInterval(intervalId);
                    intervalId = setInterval(displayNextImage, delay);
                }
        });
         plus.addEventListener('click',function (event){
             if (delay > 20) {
            delay -= 5;
             if (intervalId !== null) {
                        clearInterval(intervalId);
                        intervalId = setInterval(displayNextImage, delay);
                    }}
        });
        // Keyboard event listener
        document.addEventListener('keydown', function (event) {
            if (event.key === '+') {
                delay += 10; // Increase the delay by 100 milliseconds
                if (intervalId !== null) {
                    clearInterval(intervalId);
                    intervalId = setInterval(displayNextImage, delay);
                }
            } else if (event.key === '-') {
                if (delay > 20) { // Minimum delay of 100 milliseconds
                    delay -= 10; // Decrease the delay by 100 milliseconds
                    if (intervalId !== null) {
                        clearInterval(intervalId);
                        intervalId = setInterval(displayNextImage, delay);
                    }
                }
            }
            console.log(delay);
        });

        document.addEventListener("keydown", function (event) {
            // Check if the Ctrl key is pressed and no magnify action is in progress
            if (event.ctrlKey && !removeEventListeners) {
                // Trigger the magnify function with desired parameters and store the returned function
                removeEventListeners = magnifyCanvas("canvas", 2);
            }
        });

        document.addEventListener("keyup", function (event) {
            // Check if the Ctrl key is released and magnify action is in progress
            if (!event.ctrlKey && removeEventListeners) {
                // Call the removeEventListeners function to remove the event listeners and delete the reference
                removeEventListeners();
                removeEventListeners = null;
            }
        });

        // Slider
        sliceSlider.addEventListener('input', function (event) {
            currentImageIndex = parseInt(event.target.value);
            displayImage(currentImageIndex);
            sliderText.textContent = `${currentImageIndex}/${numSlices}`;
        });
    }


    function magnifyCanvas(canvasID, zoom) {
        var canvas, glass, w, h, bw;
        canvas = document.getElementById(canvasID);
        /*create magnifier glass:*/
        glass = document.createElement("DIV");
        glass.setAttribute("class", "canvas-magnifier-glass");
        /*insert magnifier glass:*/
        canvas.parentElement.insertBefore(glass, canvas);
        /*set background properties for the magnifier glass:*/
        glass.style.backgroundImage = "url('" + canvas.toDataURL() + "')";
        glass.style.backgroundRepeat = "no-repeat";
        glass.style.backgroundSize = (canvas.width * zoom) + "px " + (canvas.height * zoom) + "px";
        bw = 3;
        w = glass.offsetWidth / 2;
        h = glass.offsetHeight / 2;
        /*execute a function when someone moves the magnifier glass over the canvas:*/
        glass.addEventListener("mousemove", moveMagnifier);
        canvas.addEventListener("mousemove", moveMagnifier);
        /*and also for touch screens:*/
        glass.addEventListener("touchmove", moveMagnifier);
        canvas.addEventListener("touchmove", moveMagnifier);

        function moveMagnifier(e) {
            var pos, x, y;
            /*prevent any other actions that may occur when moving over the canvas*/
            e.preventDefault();
            /*get the cursor's x and y positions:*/
            pos = getCursorPos(e);
            x = pos.x;
            y = pos.y;
            /*prevent the magnifier glass from being positioned outside the canvas:*/
            if (x > canvas.width - (w / zoom)) {
                x = canvas.width - (w / zoom);
            }
            if (x < w / zoom) {
                x = w / zoom;
            }
            if (y > canvas.height - (h / zoom)) {
                y = canvas.height - (h / zoom);
            }
            if (y < h / zoom) {
                y = h / zoom;
            }
            /*set the position of the magnifier glass:*/
            glass.style.left = (x - w) + "px";
            glass.style.top = (y - h) + "px";
            /*display what the magnifier glass "sees":*/
            glass.style.backgroundPosition = "-" + ((x * zoom) - w + bw) + "px -" + ((y * zoom) - h + bw) + "px";
        }

        function getCursorPos(e) {
            var a, x = 0, y = 0;
            e = e || window.event;
            /*get the x and y positions of the canvas:*/
            a = canvas.getBoundingClientRect();
            /*calculate the cursor's x and y coordinates, relative to the canvas:*/
            x = e.pageX - a.left;
            y = e.pageY - a.top;
            /*consider any page scrolling:*/
            x = x - window.pageXOffset;
            y = y - window.pageYOffset;
            return {x: x, y: y};
        }

        // Event listener for mousemove event
        function moveMagnifierHandler(e) {
            moveMagnifier(e);
        }

        // Add event listeners
        canvas.addEventListener("mousemove", moveMagnifierHandler);
        glass.addEventListener("mousemove", moveMagnifierHandler);
        canvas.addEventListener("touchmove", moveMagnifierHandler);
        glass.addEventListener("touchmove", moveMagnifierHandler);

        return function () {
            // Remove event listeners
            canvas.removeEventListener("mousemove", moveMagnifierHandler);
            glass.removeEventListener("mousemove", moveMagnifierHandler);
            canvas.removeEventListener("touchmove", moveMagnifierHandler);
            glass.removeEventListener("touchmove", moveMagnifierHandler);
            // Remove the magnifier glass from the DOM
            glass.parentElement.removeChild(glass);
        };
    }


    function updateSliceSlider() {
        sliceSlider.value = currentImageIndex;
        sliderText.textContent = `${currentImageIndex}/${numSlices}`;

    }

    function displayNextImage() {
        displayImage(currentImageIndex);
        currentImageIndex++;
        updateSliceSlider();
        if (currentImageIndex >= numSlices) {
            currentImageIndex = 0; // Reset the index to start from the beginning
        }
    }

    function grayToRGB() {
        let index = 0;

        function processSlice() {
            const rgbaArray = new Uint8ClampedArray(standarWidth * standarHeight * 4);
            const resizedArray = resizeArray(pixelData2[index], standarWidth, standarHeight);
            const imageArrayFlat = resizedArray.flat();

            for (let i = 0; i < standarWidth * standarHeight; i++) {
                const grayValue = imageArrayFlat[i];
                const rescaledValue = Math.floor((grayValue / 255) * 255);
                const j = i * 4;
                rgbaArray[j] = rescaledValue;
                rgbaArray[j + 1] = rescaledValue;
                rgbaArray[j + 2] = rescaledValue;
                rgbaArray[j + 3] = 255;
            }

            finalArray.push(rgbaArray);
            let progress = Math.floor((finalArray.length / numSlices) * 100);
            console.log("progress ", progress);
            // Call the function to update the progress bar and percentage
            updateProgressBar(progress, finalArray.length);

            if (progress < 100) {
                index++;
                setTimeout(processSlice, 1); // Delay before processing the next slice
            } else {
                hideProgressBar();
                showDiv();
            }
        }

        processSlice();
    }


    function updateProgressBar(percentage, slice) {
        const circularProgress = document.querySelector(".circular-progress");
        const progressValue = document.querySelector(".progress-value");
        const slices = document.querySelector(".text");


        progressValue.textContent = `${percentage}%`;
        circularProgress.style.background = `conic-gradient(#0078ff ${percentage * 3.6}deg, #ededed 0deg)`;
        slices.textContent = `${slice}/${numSlices}`;
    }


    function hideProgressBar() {
        const progressBarContainer = document.getElementById('progress-container');
        progressBarContainer.style.display = 'none';
    }

    function hideCanvas() {
        const canvas = document.getElementById('canvas');
        canvas.style.display = 'none';
    }

    function showDiv() {
        var div = document.querySelector('.canvas-container');
        div.style.display = 'flex';
    }

    function displayImage(index) {
        const img = new ImageData(finalArray[index], standarWidth, standarHeight);

        // Clear the canvas before drawing the new image
        context.clearRect(0, 0, canvas.width, canvas.height);
        context.putImageData(img, 0, 0);
    }

    function resizeArray(originalArray, width, height) {
        const originalWidth = originalArray.length;
        const originalHeight = originalArray[0].length;

        const scaleX = originalWidth / width;
        const scaleY = originalHeight / height;

        const resizedArray = [];

        for (let y = 0; y < height; y++) {
            const row = [];

            for (let x = 0; x < width; x++) {
                const originalX = Math.floor(x * scaleX);
                const originalY = Math.floor(y * scaleY);

                const grayValue = originalArray[originalY][originalX];

                row.push(grayValue);
            }

            resizedArray.push(row);
        }

        return resizedArray;
    }