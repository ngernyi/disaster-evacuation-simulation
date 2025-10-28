

let listOfUsers = [];
let listToShow = [];
let currentSort = 'name-asc';
let currentKeyword = '';

window.onload = async function () {
  try {
    const response = await fetch('http://localhost:5000/get_all_users', {
      credentials: 'include',
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    const data = await response.json();

    if (data.success) {
      listOfUsers = data.users; // Use the "users" field from the backend
      updateListToShow();
      renderUsers();
    } else {
      console.error('Server returned success: false');
    }
  } catch (err) {
    console.error('Failed to fetch users:', err);
  }
};


// update list to show
function updateListToShow() {


  if (currentKeyword) {
    listToShow = listOfUsers.filter(user => 
        user.username.toLowerCase().includes(currentKeyword) ||
        user.email.toLowerCase().includes(currentKeyword)
    );
  } else {
      listToShow = [...listOfUsers]; // clone
  }

  // Sort the list
  switch (currentSort) {
    case 'name-asc':
      listToShow.sort((a, b) => a.username.localeCompare(b.username));
      break;
    case 'name-desc':
      listToShow.sort((a, b) => b.username.localeCompare(a.username));
      break;
    case 'role-admin':
      listToShow.sort((a, b) => a.role.localeCompare(b.role));
      break;
    case 'role-user':
      listToShow.sort((a, b) => b.role.localeCompare(a.role));
      break;
    default:
      break;
  }
}

function renderUsers() {
  const userListContainer = document.querySelector('.user-list');
    userListContainer.innerHTML = ''; // clear

    listToShow.forEach(user => {
        const userItem = createUserItem(user);
        userListContainer.appendChild(userItem);
    });
}

// input keywords
const searchInput = document.getElementById('searchInput');
searchInput.addEventListener('input', () => {
    currentKeyword = searchInput.value.toLowerCase();
    updateListToShow();
    renderUsers();
});

// input sort
document.querySelectorAll('#sortDropdown li').forEach(item => {
  item.addEventListener('click', () => {
      const sortType = item.dataset.sort;
      currentSort = sortType;  // Update global sort
      document.getElementById('sortBtn').textContent = 'Sort By: ' + item.textContent;
      updateListToShow();
      renderUsers();
      document.getElementById('sortDropdown').style.display = 'none';
  });
});

function promote_user(user_id) {
  fetch(`http://localhost:5000/promote_user`, {
    credentials: 'include',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ user_id: user_id })
      })
    .then(response => response.json())
    .then(result => {
    if (result.success) {
      const userIndex = listOfUsers.findIndex(user => user.id === user_id);
      if (userIndex !== -1) {
        listOfUsers[userIndex].role = 'Admin'; 
      }
       updateListToShow();
       renderUsers();
      
    } else {
      alert(`Failed to ${isPromoting ? 'promote' : 'unpromote'} the user.`);
    }
  });
}

function unpromote_user(user_id) {
  fetch(`http://localhost:5000/unpromote_user`, {
    credentials: 'include',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ user_id: user_id })
      })
    .then(response => response.json())
    .then(result => {
    if (result.success) {
      const userIndex = listOfUsers.findIndex(user => user.id === user_id);
      if (userIndex !== -1) {
        listOfUsers[userIndex].role = 'User'; 
      }
       updateListToShow();
       renderUsers();
     
    } else {
      alert(`Failed to ${isPromoting ? 'promote' : 'unpromote'} the user.`);
    }
  });
}


function ban_user(user_id) {
  fetch(`http://localhost:5000/ban_user`, {
      credentials: 'include',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ user_id: user_id })
    })
    .then(response => response.json())
    .then(result => {
      if (result.success) {
        const userIndex = listOfUsers.findIndex(user => user.id === user_id);
        if (userIndex !== -1) {
          listOfUsers[userIndex].role = 'Banned'; 
        }
       updateListToShow();
       renderUsers();
      } else {
        alert(`Failed to ban the user.`);
      }
    });
}

function unbanUser(user_id) {
  fetch(`http://localhost:5000/unban_user`, {
      credentials: 'include',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ user_id: user_id })
    })
    .then(response => response.json())
    .then(result => {
      if (result.success) {
        const userIndex = listOfUsers.findIndex(user => user.id === user_id);
        if (userIndex !== -1) {
          listOfUsers[userIndex].role = 'User'; 
        }
        updateListToShow();
        renderUsers();
      } else {
        alert(`Failed to unban the user.`);
      }
    });
}

// function to display the modal
function showConfirmModal(action, user) {
  const modal = document.getElementById('confirmModal');
  modal.style.display = 'block';
  modal.dataset.action = action;

  var needUn = false;
  // check need un or not
  if (action === 'promote') {
    if (user.role.trim() === 'Admin') {
      needUn = true;
    }
  } else if (action === 'ban') {
    if (user.role.trim() === 'Banned') {
      needUn = true;
    }
  }

  document.getElementById('confirmMessage').textContent = 
      `Are you sure you want to ${needUn? 'un' : ''}${action} ${user.username}?`;

  const cancelBtn = document.getElementById('cancelActionBtn');
  const confirmBtn = document.getElementById('confirmActionBtn');

  // Remove previous listeners if any
  cancelBtn.replaceWith(cancelBtn.cloneNode(true));
  confirmBtn.replaceWith(confirmBtn.cloneNode(true));

  // Get new button elements (after clone)
  const newCancelBtn = document.getElementById('cancelActionBtn');
  const newConfirmBtn = document.getElementById('confirmActionBtn');

  // if cancel is clicked
  newCancelBtn.addEventListener('click', () => {
    modal.style.display = 'none';
   
  });

  // if confirm is clicked
  newConfirmBtn.addEventListener('click', () => {
    // promote or ban
    if (action === 'promote') {
      if (needUn) {
        unpromote_user(user.id);
      } else {
        promote_user(user.id);
      }
    } else if (action === 'ban') {
      if (needUn) {
        unbanUser(user.id);
      } else {
        ban_user(user.id);
      }
    }
    modal.style.display = 'none';
   
  });

}


// Helper to create a user item
function createUserItem(user) {
  const item = document.createElement('div');
  item.className = 'user-item';

  const userInfo = document.createElement('div');
  userInfo.className = 'user-info';
  userInfo.innerHTML = `
    <h3 class="username">${user.username}</h3>
    <p class="email">${user.email}</p>
  `;

  const userActions = document.createElement('div');
  userActions.className = 'user-actions';

  // Promote/Unpromote button
  const promoteBtn = document.createElement('button');
  promoteBtn.className = 'btn promote-btn';
  promoteBtn.textContent = user.role.trim() === 'Admin' ? 'Unpromote' : 'Promote';
  promoteBtn.style.backgroundColor = user.role.trim() === 'Admin' ? '#808080' : '#4CAF50';
  promoteBtn.addEventListener('click', () => {
   showConfirmModal('promote', user);
  });

  // Ban/Unban button
  const banBtn = document.createElement('button');
  banBtn.className = 'btn ban-btn';
  banBtn.textContent = user.role.trim() === 'Banned' ? 'Unban' : 'Ban';
  banBtn.style.backgroundColor = user.role.trim() === 'Banned' ? '#ff6666' : '';
  banBtn.addEventListener('click', () => {
   showConfirmModal('ban', user);
  });

  const number_of_simulations = document.createElement('p');
  number_of_simulations.className = 'number_of_simulations';
  number_of_simulations.textContent = `Number of Simulations: ${user.number_of_simulations}`;
  userActions.appendChild(number_of_simulations);
  userActions.appendChild(promoteBtn);
  userActions.appendChild(banBtn);

  

  item.appendChild(userInfo);
  item.appendChild(userActions);

  return item;
}

document.getElementById('genSimBtn').addEventListener('click', function() {
  window.location.href = 'http://localhost:5501/Code/frontend/html/landingPage.html';
});


// Sort dropdown toggle
const sortBtn = document.getElementById('sortBtn');
sortBtn.addEventListener('click', () => {
  const dropdown = document.getElementById('sortDropdown');
  dropdown.style.display = dropdown.style.display === 'block' ? 'none' : 'block';
  const rect = sortBtn.getBoundingClientRect();
  dropdown.style.position = dropdown.style.position = 'absolute';
  dropdown.style.left = `${rect.left}px`;
  dropdown.style.top = `${rect.bottom}px`;
});




