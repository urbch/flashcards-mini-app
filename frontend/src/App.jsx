import { useEffect, useState } from 'react';
import TelegramWebApp from '@twa-dev/sdk';
import './App.css';

function App() {
  const [user, setUser] = useState(null);
  const [decks, setDecks] = useState([]);
  const [deckName, setDeckName] = useState('');

  useEffect(() => {
    TelegramWebApp.ready();
    setUser(TelegramWebApp.initDataUnsafe.user);
  }, []);

  const fetchDecks = async () => {
    if (user) {
      try {
        const response = await fetch(`https://3291-194-58-154-209.ngrok-free.app/${user.id}`);
        const data = await response.json();
        setDecks(data);
      } catch (error) {
        console.error('Error fetching decks:', error);
      }
    }
  };

  const createDeck = async () => {
    if (user && deckName) {
      try {
        const response = await fetch('http://localhost:8000/decks/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: user.id, name: deckName }),
        });
        const newDeck = await response.json();
        setDecks([...decks, newDeck]);
        setDeckName('');
      } catch (error) {
        console.error('Error creating deck:', error);
      }
    }
  };

  useEffect(() => {
    fetchDecks();
  }, [user]);

  return (
    <div className="App">
      <h1>Flashcards Mini App</h1>
      {user ? <p>Привет, {user.first_name}!</p> : <p>Загрузка...</p>}
      <div>
        <input
          type="text"
          value={deckName}
          onChange={(e) => setDeckName(e.target.value)}
          placeholder="Название колоды"
        />
        <button onClick={createDeck}>Создать колоду</button>
      </div>
      <h2>Ваши колоды:</h2>
      <ul>
        {decks.map((deck) => (
          <li key={deck.id}>{deck.name}</li>
        ))}
      </ul>
    </div>
  );
}

export default App;