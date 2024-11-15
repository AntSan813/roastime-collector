// document.addEventListener("DOMContentLoaded", function () {
//   const urlParams = new URLSearchParams(window.location.search)
//   const beanId = urlParams.get("bean_id")
//   const openModal = urlParams.get("open_modal")

//   if (beanId) {
//     document.getElementById("beanId").value = beanId
//     document.getElementById("beanFormModalLabel").textContent = "Edit Bean"
//   } else {
//     document.getElementById("beanFormModalLabel").textContent = "Add Bean"
//   }

//   if (openModal === "true") {
//     beanFormModal.show()
//   }
// })

// function clearForm() {
//   document.getElementById("beanForm").reset()
//   document.getElementById("beanFormModalLabel").textContent = "Add Bean"
// }

// TODO: for bean profile, update content on screen after update... or force reload
// function editBean(beanId) {
//   const beans = JSON.parse(document.getElementById("beans-data").textContent)
//   const selectedBean = beans.find(b => b.id === beanId)

//   if (selectedBean) {
//     document.getElementById("beanId").value = selectedBean.id
//     document.getElementById("name").value = selectedBean.name
//     document.getElementById("origin").value = selectedBean.origin
//     document.getElementById("region").value = selectedBean.region
//     document.getElementById("varietal").value = selectedBean.varietal
//     document.getElementById("processing_method").value =
//       selectedBean.processing_method
//     document.getElementById("altitude").value = selectedBean.altitude
//     document.getElementById("taste_notes").value = selectedBean.taste_notes
//     document.getElementById("aroma").value = selectedBean.aroma
//     document.getElementById("acidity").value = selectedBean.acidity
//     document.getElementById("brew_methods").value = selectedBean.brew_methods
//     document.getElementById("cupping_score").value = selectedBean.cupping_score
//     document.getElementById("certifications").value =
//       selectedBean.certifications

//     document.getElementById("beanFormModalLabel").textContent = "Edit Bean"
//     beanFormModal.show()
//   }
// }

// document
//   .getElementById("beanForm")
//   .addEventListener("submit", function (event) {
//     event.preventDefault()
//     const formData = new FormData(this)
//     const beanId = document.getElementById("beanId").value
//     const url = beanId ? `/edit_bean/${beanId}` : "/add_bean"
//     const method = beanId ? "PUT" : "POST"

//     fetch(url, {
//       method: method,
//       body: formData,
//     })
//       .then(response => response.json())
//       .then(data => {
//         if (
//           data.message === "Bean added successfully" ||
//           data.message === "Bean updated successfully"
//         ) {
//           // alert(data.message)
//           updateBeanCard(beanId)
//           beanFormModal.hide()
//         } else {
//           alert("Failed to save bean.")
//         }
//       })
//   })

// function updateBeanCard(beanId) {
//   fetch(`/bean_card/${beanId}`)
//     .then(response => response.text())
//     .then(html => {
//       const parser = new DOMParser()
//       const doc = parser.parseFromString(html, "text/html")

//       const oldBeanCard = document.getElementById(`bean-card-${beanId}`)
//       if (oldBeanCard && newBeanCard) {
//         const newBeanCard = doc.body.firstElementChild
//         oldBeanCard.replaceWith(newBeanCard)
//       }
//     })
// }

// function searchRoasts() {
//   const input = document.getElementById("searchInput").value.toLowerCase()
//   const roastCards = document.querySelectorAll(
//     "#roast-cards-container .col-md-6"
//   )
//   let anyVisible = false

//   roastCards.forEach(card => {
//     const roastName = card
//       .querySelector(".card-title")
//       .textContent.toLowerCase()
//     if (roastName.includes(input)) {
//       card.style.display = ""
//       anyVisible = true
//     } else {
//       card.style.display = "none"
//     }
//   })

//   document.getElementById("no-results").style.display = anyVisible
//     ? "none"
//     : "block"
// }
