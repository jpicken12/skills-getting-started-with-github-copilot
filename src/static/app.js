document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <div class="participants-section">
            <strong>Participants:</strong>
            <div class="participants-list"></div>
          </div>
        `;

        activitiesList.appendChild(activityCard);

        // Populate participants with delete buttons
        const participantsList = activityCard.querySelector(".participants-list");
        if (details.participants.length > 0) {
          details.participants.forEach((participant) => {
            const participantItem = document.createElement("div");
            participantItem.className = "participant-item";
            participantItem.innerHTML = `
              <span>${participant}</span>
              <button class="delete-btn" data-activity="${name}" data-email="${participant}" title="Remove participant">
                🗑
              </button>
            `;
            participantsList.appendChild(participantItem);
          });
        } else {
          participantsList.innerHTML = "<p class='no-participants'>No participants yet</p>";
        }

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Event delegation for delete buttons
  activitiesList.addEventListener("click", async (event) => {
    if (event.target.classList.contains("delete-btn")) {
      event.preventDefault();
      const btn = event.target;
      const activity = btn.getAttribute("data-activity");
      const email = btn.getAttribute("data-email");

      try {
        const response = await fetch(
          `/activities/${encodeURIComponent(activity)}/unregister?email=${encodeURIComponent(email)}`,
          {
            method: "DELETE",
          }
        );

        console.log("Delete response status:", response.status, "ok:", response.ok);

        if (response.ok || response.status === 200) {
          try {
            btn.parentElement.remove();
            // Check if participants list is now empty
            const participantsList = btn.closest(".participants-section")?.querySelector(".participants-list");
            if (participantsList?.children.length === 0) {
              participantsList.innerHTML = "<p class='no-participants'>No participants yet</p>";
            }
          } catch (domError) {
            console.error("DOM manipulation error:", domError);
          }
          
          try {
            await fetchActivities(); // Refresh activities to update availability count
          } catch (fetchError) {
            console.error("Error refreshing activities:", fetchError);
          }
        } else {
          const result = await response.json();
          console.log("Delete error response:", result);
          alert(result.detail || "Failed to remove participant");
        }
      } catch (error) {
        console.error("Error removing participant:", error);
        alert("Failed to remove participant. Please try again.");
      }
    }
  });

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();
        fetchActivities(); // Refresh activities to show the new participant
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  fetchActivities();
});
