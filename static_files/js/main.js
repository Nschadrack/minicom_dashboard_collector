window.onload=function(){
    var car_title_header_button_clicked = document.getElementById("car_title_header_and_new_btn_button");
    // var cancelOperation = document.getElementById("cancel_operation");
    var groupCarRegisterForm = document.getElementsByClassName("car_new_form");

    /* Group car page function call */
    car_title_header_button_clicked.addEventListener('click', showNewGroupCarRegiseterForm);
    // cancelOperation.addEventListener('click', showGroupCarList);
}


// Tabs
document.addEventListener("DOMContentLoaded", function() {
    const tabLinks = document.querySelectorAll('.tab-link');
    const tabContents = document.querySelectorAll('.tab-content');

    tabLinks.forEach(tab => {
        tab.addEventListener('click', function() {
            const targetTab = this.getAttribute('data-tab');

            // Remove active class from all tabs and contents
            tabLinks.forEach(tab => tab.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            // Add active class to the clicked tab and corresponding content
            this.classList.add('active');
            document.getElementById(targetTab).classList.add('active');
        });
    });

    // Get the hash from the URL (e.g., #companies-industries-in-parks)
    const hash = window.location.hash.substring(1); // Remove the '#' from the hash

    if (hash) {
        // Deactivate all tabs and content
        document.querySelectorAll('.tab-link').forEach(tab => tab.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

        // Activate the matching tab and content if they exist
        const tab = document.querySelector(`.tab-link[data-tab="${hash}"]`);
        const content = document.getElementById(hash);

        if (tab && content) {
            tab.classList.add('active');
            content.classList.add('active');
            content.scrollIntoView({ behavior: 'smooth' });
        }
    };

    // uplaoding documents
    document.addEventListener('change', function(e) {
        if (e.target.matches('input[type="file"]')) {
            const tabContainer = e.target.closest('.tab-content');
            const fileNameSpan = tabContainer.querySelector('.file-name');
            const uploadContainer = tabContainer.querySelector('.upload-container');
    
            if (e.target.files.length > 0) {
                fileNameSpan.textContent = e.target.files[0].name;
                uploadContainer.classList.add('file-selected');
                uploadContainer.style.borderColor = '#0066cc';
            } else {
                fileNameSpan.textContent = '';
                uploadContainer.classList.remove('file-selected');
                uploadContainer.style.borderColor = '#ccc';
            }
        }
    });

    // Optional: Add drag and drop highlight
    uploadContainer.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadContainer.style.borderColor = '#0066cc';
        uploadContainer.style.backgroundColor = '#e9f5ff';
    });
    
    uploadContainer.addEventListener('dragleave', (e) => {
        e.preventDefault();
        if (!fileInput.files.length) {
            uploadContainer.style.borderColor = '#ccc';
            uploadContainer.style.backgroundColor = '#f8f9fa';
        }
    });
});

function showNewGroupCarRegiseterForm(e){
    var form_div_to_shows = document.getElementsByClassName("car_new_form_div");
    var car_list_to_hide = document.getElementById("car_table_data");
    var car_title_header_button_clicked = document.getElementById("car_title_header_and_new_btn_button");
    var car_title_header_paragraph = document.getElementById("car_title_header_and_new_btn_p");

    Array.from(form_div_to_shows).forEach((form_div_to_show) =>{
        form_div_to_show.style.display="block";
    });
    car_list_to_hide.style.display = "none";
    car_title_header_button_clicked.style.display="none";
    car_title_header_paragraph.style.display="none";
}

function hideNewGroupCarRegiseterForm(e){
    var form_div_to_shows = document.getElementsByClassName("car_new_form_div");
    var car_list_to_hide = document.getElementById("car_table_data");
    var car_title_header_button_clicked = document.getElementById("car_title_header_and_new_btn_button");
    var car_title_header_paragraph = document.getElementById("car_title_header_and_new_btn_p");

    var assignmentTables = document.getElementsByClassName("new-assignment");
    var upperDivs = document.getElementsByClassName("upper-detail-div");

    // Convert HTMLCollection to an array before using forEach
    if(upperDivs != null){
        Array.from(upperDivs).forEach((upperDiv) => {
            upperDiv.style.display = "block";
        });
    }

    if(assignmentTables != null){
        Array.from(assignmentTables).forEach((assignmentTable) => {
            assignmentTable.style.display = "none";
        });
    }

    Array.from(form_div_to_shows).forEach((form_div_to_show) =>{
        form_div_to_show.style.display="none";
    });

    if(car_list_to_hide != null){
        car_list_to_hide.style.display = "block";
    }
    if(car_title_header_button_clicked != null){
        car_title_header_button_clicked.style.display="block";
    }
    if(car_title_header_paragraph != null){
        car_title_header_paragraph.style.display="block";
    }
    
}

function showUserRegistrationForm(e){
    var user_login_form = document.getElementById("login-form");
    var user_register_form = document.getElementById("registration-form");

    user_login_form.style.display="none";
    user_register_form.style.display = "block";
}
function showUserLoginForm(e){
    var user_login_form = document.getElementById("login-form");
    var user_register_form = document.getElementById("registration-form");

    user_login_form.style.display="block";
    user_register_form.style.display = "none";
}
function toggleAssetRegistrySection(e){
    var assets_registry_section = document.getElementById("assets-registry-section");
    var style = window.getComputedStyle(assets_registry_section);
    var displayCss = style.getPropertyValue("display")
    if (displayCss === "none"){
        assets_registry_section.style.display = "block";
    }else{
        assets_registry_section.style.display = "none";
    }
    
}

function toggleDashboardsSection(e){
    var dashboardsSection = document.getElementById("dashboards-section");
    var style = window.getComputedStyle(dashboardsSection);
    var displayCss = style.getPropertyValue("display")
    if (displayCss === "none"){
        dashboardsSection.style.display = "block";
    }else{
        dashboardsSection.style.display = "none";
    }
}

function toggleUsersManagementAssetSection(e){
    var users_management_section = document.getElementById("users-management-section");
    var style = window.getComputedStyle(users_management_section);
    var displayCss = style.getPropertyValue("display")
    if (displayCss === "none"){
        users_management_section.style.display = "block";
    }else{
        users_management_section.style.display = "none";
    }
}

function showSparepartsWindows(e){
    var sparepartaddButton = document.getElementById("add-sparepart-button");
    var sparepartWindow = document.getElementById("spareparts_div");
    sparepartWindow.style.display = "block";
}
function hideSparepartsWindows(e){
    var sparepartaddButton = document.getElementById("add-sparepart-button");
    var sparepartWindow = document.getElementById("spareparts_div");
    sparepartWindow.style.display = "none";
}

function fillSparepartSelectBox(e){
    var spareparts = document.getElementById("spareparts");
    var selectedSparepart = document.getElementById("partnumber").value;
    spareparts.style.display = "block";
    spareparts.innerHTML += `<option value="${selectedSparepart}" selected>${selectedSparepart}</option>`;    
}
function toggleNavigations(e){
    var navigationDiv = document.getElementById("aside_navigation");
    var mainLoadDiv = document.getElementById("main_load");
    var mainLoadHeader = document.getElementById("main_load_header");
    var styleNav = window.getComputedStyle(navigationDiv);
    var displayCssNav = styleNav.getPropertyValue("display")

    if (displayCssNav === "none"){
        navigationDiv.style.display = "block";
        navigationDiv.style.width = "20%";
        mainLoadDiv.style.width = "80%";
        mainLoadHeader.style.left = "20%";
    }else{
        navigationDiv.style.display = "none";
        mainLoadDiv.style.width = "100%";
        mainLoadHeader.style.left = "0px";
    }

}

function showAssignmentTable(value){
    var assignmentTables = document.getElementsByClassName("new-assignment");
    var upperDivs = document.getElementsByClassName("upper-detail-div");

    // Convert HTMLCollection to an array before using forEach
    Array.from(upperDivs).forEach((upperDiv) => {
        upperDiv.style.display = value === "block" ? "none" : "block";
    });

    Array.from(assignmentTables).forEach((assignmentTable) => {
        assignmentTable.style.display = value;
    });
}

/* fill in data */
function fillInZones(data){
    let loaded_zones= JSON.parse(data);
    let parkField = document.getElementById("parks_fill_field");
    let targetedZoneField = document.getElementById("zones_fill_field");
    let selectedIndex = parkField.selectedIndex;
    let selectIndexValue = parkField.options[selectedIndex].value;

    targetedZoneField.innerHTML = "<option disabled selected>choose zoning</option>"
    for(const element of loaded_zones) {
        if (element.park_id.toString() === selectIndexValue) {
            targetedZoneField.innerHTML += `<option value="${element.id}">${element.name}</option>}`
        }
    }
}
function fillInZonesDataList(data){
    let loaded_zones= JSON.parse(data);
    let parkField = document.getElementById("parks_fill_field");
    let targetedZoneField = document.getElementById("zones_fill_field");
    let selectedIndex = parkField.selectedIndex;
    let selectIndexValue = parkField.options[selectedIndex].value;

    targetedZoneField.innerHTML = ""
    for(const element of loaded_zones) {
        if (element.park_id.toString() === selectIndexValue) {
            targetedZoneField.innerHTML += `<option value="${element.id}-${element.name}"></option>`
        }
    }
}

function fillInLandRequestPartitionedPlots(data){
    let loaded_plots = JSON.parse(data);
    let zoneField = document.getElementById("zones_fill_field");
    let targetedPartitionedPlotTable= document.getElementById("land_request_candidate_partitioned_plots");
    let selectedIndex = zoneField.selectedIndex;
    let selectIndexValue = zoneField.options[selectedIndex].value;
    let countPlots = 0;

    targetedPartitionedPlotTable.innerHTML = ""
    for(const element of loaded_plots) {
        if (element.zone_id.toString() === selectIndexValue) {
            countPlots += 1;
            targetedPartitionedPlotTable.innerHTML += `
                <tr>
                    <td><input type="checkbox" id="${element.id}" name="partitioned_plots[]" value="${ element.id }"></td>
                    <td style="text-align: left; padding-left: 20px;"><label for="${element.id}">${element.plot_number}</label></td>
                    <td><label for="${element.id}">${element.plot_upi}</td>
                    <td style="text-align: left; padding-left: 20px;"><label for="${element.id}">${element.plot_size} m<sup>2</sup></label></td>
                    <td style="text-align: left; padding-left: 20px;"><label for="${element.id}">${element.zone_name}</label></td>
                </tr>
            `
        }
    }

    if (countPlots == 0){
        targetedPartitionedPlotTable.innerHTML = "<p>There are no partitioned plots in the selected zone";
    }
}

function AddOtherSupportingDocumentFieldName(e){
    let attachmentCategory= document.getElementById("industry-document-attachment");
    let targetFieldDiv = document.getElementById("other-supporting-document-name");
    let selectedCategoryIndex = attachmentCategory.selectedIndex;
    let selectedCategoryIndexValue = attachmentCategory.options[selectedCategoryIndex].value;

    if (selectedCategoryIndexValue == "Other Supporting Document"){
        console.log("Other documents");
        targetFieldDiv.innerHTML = `
        <label>Give the document a name <b>[required]</b></label>
        <input type="text" name="name" maxlength="100" required/>
        `;
    }else{
        targetFieldDiv.innerHTML = "";
    }
}

function fillInDistricts(data){
    let loaded_districts = JSON.parse(data);
    let districtProvince = document.getElementById("exampleInputProvince");
    let targetedDistricts = document.getElementById("exampleInputDistrict");
    let selectedIndex = districtProvince.selectedIndex;
    let selectIndexValue = districtProvince.options[selectedIndex].value;

     targetedDistricts.innerHTML = "<option disabled selected>choose district</option>"
    for(const element of loaded_districts) {
        if (element.parent_id.toString() === selectIndexValue) {
            targetedDistricts.innerHTML += `<option value="${element.id}">${element.name}</option>}`
        }
    }
}
function fillInSectors(data){
    let loaded_sectors = JSON.parse(data);
    let districtSelected = document.getElementById("exampleInputDistrict");
    let targetedSectors = document.getElementById("exampleInputSector");
    let selectedIndex = districtSelected.selectedIndex;
    let selectIndexValue = districtSelected.options[selectedIndex].value;

     targetedSectors.innerHTML = "<option disabled selected>choose sector</option>"
    for(const element of loaded_sectors) {
        if (element.parent_id.toString() === selectIndexValue) {
            targetedSectors.innerHTML += `<option value="${element.id}">${element.name}</option>}`
        }
    }
}

function fillInCells(data){
    let loaded_cells = JSON.parse(data);
    let sectorSelected = document.getElementById("exampleInputSector");
    let targetedCells = document.getElementById("exampleInputCell");
    let selectedIndex = sectorSelected.selectedIndex;
    let selectIndexValue = sectorSelected.options[selectedIndex].value;

     targetedCells.innerHTML = "<option disabled selected>choose cell</option>"
    for(const element of loaded_cells) {
        if (element.parent_id.toString() === selectIndexValue) {
            targetedCells.innerHTML += `<option value="${element.id}">${element.name}</option>}`
        }
    }
}

// multi selection
function handleSelection(selectedValue, hiddenFieldId, tagsContainerId) {
    const hiddenInput = document.getElementById(hiddenFieldId);
    const selectedItems = hiddenInput.value ? hiddenInput.value.split(',') : [];
    
    if (!selectedItems.includes(selectedValue)) {
        selectedItems.push(selectedValue);
        hiddenInput.value = selectedItems.join(',');
        
        const tag = document.createElement('div');
        tag.className = 'item-tag';
        tag.innerHTML = `
            ${selectedValue}
            <span class="remove-btn" 
                  onclick="removeItem('${selectedValue}', '${hiddenFieldId}', '${tagsContainerId}')">
                ×
            </span>
        `;
        document.getElementById(tagsContainerId).appendChild(tag);
    }
}

function showDropdown(dropdownId, passedItems, hiddenFieldId, tagsContainerId, parentId) {
    const searchInput = document.getElementById(dropdownId.replace('Dropdown', 'Search'));
    filterDropdown(dropdownId, passedItems, hiddenFieldId, tagsContainerId, searchInput.value, parentId);
}

function filterDropdown(dropdownId, passedItems, hiddenFieldId, tagsContainerId, searchTerm, parentId) {
    let items = JSON.parse(passedItems);

    if (parentId !== "none") {
        let parentSelection = document.getElementById(parentId);
        let selectedIndex = parentSelection.selectedIndex;
        let selectedIndexValue = parentSelection.options[selectedIndex].value;

        items = items.filter((item) => {
            const [id, itemName, parent] = item.split("|"); // Corrected destructuring
            return parent.toString() === selectedIndexValue;
        });
    }

    
    const hiddenInput = document.getElementById(hiddenFieldId);
    const selectedItems = hiddenInput.value ? hiddenInput.value.split(',') : [];
    
    const filteredItems = items.filter(item => 
        !selectedItems.includes(item) &&
        item.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const dropdown = document.getElementById(dropdownId);
    dropdown.innerHTML = '';
    
    filteredItems.forEach(item => {
        const div = document.createElement('div');
        div.className = 'dropdown-item';
        div.textContent = item;
        div.onclick = () => {
            handleSelection(item, hiddenFieldId, tagsContainerId);
            dropdown.style.display = 'none';
        };
        dropdown.appendChild(div);
    });
    
    dropdown.style.display = filteredItems.length > 0 ? 'block' : 'none';
}

function removeItem(item, hiddenFieldId, tagsContainerId) {
    const hiddenInput = document.getElementById(hiddenFieldId);
    const selectedItems = hiddenInput.value.split(',')
        .filter(i => i !== item);
    
    hiddenInput.value = selectedItems.join(',');
    
    const tagsContainer = document.getElementById(tagsContainerId);
    Array.from(tagsContainer.children).forEach(tag => {
        if (tag.textContent.includes(item)) {
            tag.remove();
        }
    });
}

// Close dropdown when clicking outside
document.addEventListener('click', (e) => {
    if (!e.target.closest('.select-container')) {
        document.querySelectorAll('.dropdown').forEach(d => d.style.display = 'none');
    }
});

// copying the text
function copyText() {
    let text = document.getElementById("myInputToCopy").value;
    let alertP = document.getElementById("copyAlertMessage");
    navigator.clipboard.writeText(text).then(() => {
        alertP.innerHTML = "Copied to clipboard! <button onclick='closeCopyTextAlert();' id='closebtnCopyText'>X</button>";
        alertP.style.display = "block";
    }).catch(err => {
        alertP.innerHTML = "Failed to copy! <button onclick='closeCopyTextAlert();' id='closebtnCopyText'>X</button>";
        alertP.style.display = "block";
    });
}

function copyText2() {
    let textInput = document.getElementById("myInputToCopy2");
    let text = textInput.value
    let alertP = document.getElementById("copyAlertMessage2");
    navigator.clipboard.writeText(text).then(() => {
        alertP.innerHTML = "Copied to clipboard! <button onclick='closeCopyTextAlert2();' id='closebtnCopyText2'>X</button>";
        alertP.style.display = "block";
    }).catch(err => {
        alertP.innerHTML = "Failed to copy! <button onclick='closeCopyTextAlert2();' id='closebtnCopyText2'>X</button>";
        alertP.style.display = "block";
    });
}

function closeCopyTextAlert(){
    let alertP = document.getElementById("copyAlertMessage");
    alertP.style.display="none";

}

function closeCopyTextAlert2(){
    let alertP = document.getElementById("copyAlertMessage2");
    alertP.style.display="none";

}
function showPaymentRefund(){
    let refundDiv = document.getElementById("refund-form-payment");
    let refundWarningDiv = document.getElementById("refund-warning-div");

    refundWarningDiv.style.display="none";
    refundDiv.style.display="block";
}
function hidePaymentRefund(){
    let refundDiv = document.getElementById("refund-form-payment");
    let refundWarningDiv = document.getElementById("refund-warning-div");

    refundWarningDiv.style.display="block";
    refundDiv.style.display="none";
}

