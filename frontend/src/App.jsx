
import { useEffect, useState } from 'react';
import TelegramWebApp from '@twa-dev/sdk';
import './App.css';

function App() {
  const [user, setUser] = useState(null);
  const [decks, setDecks] = useState([]);
  const [deckName, setDeckName] = useState('');
  const [showDecks, setShowDecks] = useState(false);

  const fetchUserInfo = async (telegramId) => {
    try {
      const response = await fetch(`https://befb-194-58-154-209.ngrok-free.app/user/${telegramId}/`);
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      const data = await response.json();
      console.log('Fetched user info:', data);
      return data;
    } catch (error) {
      console.error('Error fetching user info:', error);
      return { id: telegramId, first_name: 'Guest' }; // Запасной вариант
    }
  };

  useEffect(() => {
    TelegramWebApp.ready();
    const initDataRaw = TelegramWebApp.initData;
    const initData = TelegramWebApp.initDataUnsafe;
    console.log('Raw initData:', initDataRaw);
    console.log('Parsed initData:', JSON.stringify(initData, null, 2));
    console.log('Telegram version:', TelegramWebApp.version);
    console.log('Platform:', TelegramWebApp.platform);

    const setUserData = async () => {
      if (initData && initData.user) {
        setUser(initData.user);
        console.log('User set from initData:', initData.user);
      } else {
        console.warn('No user data in initData, falling back to URL parameter');
        const urlParams = new URLSearchParams(window.location.search);
        const telegramIdFromUrl = urlParams.get('telegram_id');
        if (telegramIdFromUrl) {
          const telegramId = parseInt(telegramIdFromUrl);
          const userInfo = await fetchUserInfo(telegramId);
          setUser(userInfo);
          console.log('Set user from fetched info:', userInfo);
        } else {
          console.error('No user data in initData or URL:', initData);
        }
      }
    };

    setUserData();
  }, []);

  useEffect(() => {
    console.log('Decks state updated:', decks);
  }, [decks]);

  const fetchDecks = async () => {
    if (!user || !user.id) {
      console.error('No user ID available for fetching decks');
      return;
    }
    try {
      const response = await fetch(`https://befb-194-58-154-209.ngrok-free.app/decks/${user?.id}`, {
      method: "get",
      headers: new Headers({
        "ngrok-skip-browser-warning": "69420",
      }),
    });
      console.log('Status:', response.status);
      const contentType = response.headers.get("content-type");
      console.log('Content-Type:', contentType);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Error response:', errorText);
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      if (contentType && contentType.includes("application/json")) {
        const data = await response.json();
        console.log('Received decks data:', data);
        setDecks(data);
      } else {
        const textData = await response.text();
        console.warn('Expected JSON but got:', textData);
      }
    } catch (error) {
      console.error('Error fetching decks:', error);
    }
  };

  const createDeck = async () => {
    if (!user || !user.id || !deckName || !deckName.trim()) {
      console.error('Cannot create deck: invalid data', { user, deckName });
      return;
    }
    const payload = { telegram_id: user.id, name: deckName.trim() };
    console.log('Sending to /decks/:', payload);
    try {
      const response = await fetch('https://befb-194-58-154-209.ngrok-free.app/decks/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        const errorData = await response.json();
        console.error('Error response:', errorData);
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      setDeckName('');
      if (showDecks) {
        await fetchDecks();
      }
    } catch (error) {
      console.error('Error creating deck:', error);
    }
  };

  const handleShowDecks = async () => {
    console.log('Show decks toggled, current showDecks:', showDecks);
    if (!showDecks) {
      await fetchDecks();
    }
    setShowDecks(!showDecks);
  };

  if (!user) {
    return <p>Не удалось загрузить данные пользователя. Пожалуйста, перезапустите бота или проверьте настройки.</p>;
  }

  return (
    <div className="App">
      <h1>Flashcards Mini App</h1>
      <p>Привет!</p>
      <div>
        <input
          type="text"
          value={deckName}
          onChange={(e) => setDeckName(e.target.value)}
          placeholder="Название колоды"
        />
        <button onClick={createDeck}>Создать колоду</button>
      </div>
      <div>
        <button onClick={handleShowDecks}>
          {showDecks ? 'Скрыть колоды' : 'Мои колоды'}
        </button>
      </div>
      {showDecks && (
        <>
          <h2>Ваши колоды:</h2>
          <ul>
            {decks.length > 0 ? (
              decks.map((deck) => <li key={deck.id}>{deck.name}</li>)
            ) : (
              <p>У вас пока нет колод.</p>
            )}
          </ul>
        </>
      )}
    </div>
  );
}

export default App;