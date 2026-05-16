const grid = document.getElementById('grid');
const loading = document.getElementById('loading');
const searchInput = document.getElementById('search');

let allPokemon = [];


const pokemonNames = ["bulbasaur", "ivysaur", "venusaur", "metapod", "butterfree", "weedle"];

async function fetchPokemon() {
  try {
    loading.textContent = "Загрузка покемонов...";

    const promises = pokemonNames.map(async (name) => {
      const res = await fetch(`https://pokeapi.co/api/v2/pokemon/${name}`);
      if (!res.ok) throw new Error(`Не найден: ${name}`);
      return res.json();
    });

    allPokemon = await Promise.all(promises);
    displayPokemon(allPokemon);
  } catch (err) {
    console.error(err);
    loading.textContent = 'Ошибка загрузки Попробуй обновить страницу';
  }
}

function displayPokemon(pokemonList) {
  loading.style.display = 'none';
  grid.innerHTML = '';

  pokemonList.forEach(p => {
    const card = document.createElement('div');
    card.className = 'card';

    const imgSrc = p.sprites.other?.['official-artwork']?.front_default || 
                   p.sprites.front_default || 
                   'https://via.placeholder.com/85?text=No+Image';

    const typesHTML = p.types.map(t => 
      `<span class="type ${t.type.name}">${t.type.name}</span>`
    ).join('');

    card.innerHTML = `
      <img src="${imgSrc}" alt="${p.name}">
      <div class="info">
        <h3>#${String(p.id).padStart(3, '0')}</h3>
        <h2>${p.name}</h2>
        <div class="types">${typesHTML}</div>
      </div>
    `;

    grid.appendChild(card);
  });
}

searchInput.addEventListener('input', () => {
  const term = searchInput.value.toLowerCase().trim();
  const filtered = allPokemon.filter(p => 
    p.name.toLowerCase().includes(term)
  );
  displayPokemon(filtered);
});

fetchPokemon();