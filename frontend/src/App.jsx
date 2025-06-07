//
// import { useEffect, useState } from 'react';
// import TelegramWebApp from '@twa-dev/sdk';
// import { useSwipeable } from 'react-swipeable';
// import './App.css';
//
// function App() {
//   const [user, setUser] = useState(null);
//   const [decks, setDecks] = useState([]);
//   const [deckName, setDeckName] = useState('');
//   const [showDecks, setShowDecks] = useState(false);
//   const [selectedDeck, setSelectedDeck] = useState(null);
//   const [cards, setCards] = useState([]);
//
//   // окно редактирования карточек
//   const [showCardModal, setShowCardModal] = useState(false);
//   const [cardRows, setCardRows] = useState([]);
//
//   // Режим изучения
//   const [studyMode, setStudyMode] = useState(false);
//   const [currentCardIndex, setCurrentCardIndex] = useState(0);
//   const [isFlipped, setIsFlipped] = useState(false);
//   const [swipeDirection, setSwipeDirection] = useState(null);
//
//   // Новые состояния для результатов
//   const [correctCount, setCorrectCount] = useState(0);
//   const [incorrectCount, setIncorrectCount] = useState(0);
//   const [finishedStudy, setFinishedStudy] = useState(false);
//
//   const [isLanguageDeck, setIsLanguageDeck] = useState(false);
//   const [sourceLang, setSourceLang] = useState('');
//   const [targetLang, setTargetLang] = useState('');
//   const [languages, setLanguages] = useState([]);
//   const [isLanguageDeckSelected, setIsLanguageDeckSelected] = useState(false);
//
//   const fetchUserInfo = async (telegramId) => {
//     try {
//       const response = await fetch(`https://f09b-194-58-154-209.ngrok-free.app/user/${telegramId}/`);
//       if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
//       const data = await response.json();
//       return data;
//     } catch (error) {
//       console.error('Error fetching user info:', error);
//       return { id: telegramId, first_name: 'Guest' };
//     }
//   };
//
//   const fetchLanguages = async () => {
//     try {
//       const response = await fetch(`https://f09b-194-58-154-209.ngrok-free.app/languages/`, {
//         headers: { 'ngrok-skip-browser-warning': '69420' },
//       });
//       if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
//       const data = await response.json();
//       setLanguages(data);
//     } catch (error) {
//       console.error('Error fetching languages:', error);
//     }
//   };
//
//   useEffect(() => {
//     TelegramWebApp.ready();
//     const initData = TelegramWebApp.initDataUnsafe;
//
//     const setUserData = async () => {
//       if (initData && initData.user) {
//         setUser(initData.user);
//       } else {
//         const urlParams = new URLSearchParams(window.location.search);
//         const telegramIdFromUrl = urlParams.get('telegram_id');
//         if (telegramIdFromUrl) {
//           const telegramId = parseInt(telegramIdFromUrl);
//           const userInfo = await fetchUserInfo(telegramId);
//           setUser(userInfo);
//         } else {
//           console.error('No user data in initData or URL');
//         }
//       }
//     };
//
//     setUserData();
//     fetchLanguages();
//   }, []);
//
//   const fetchDecks = async () => {
//     if (!user?.id) return;
//     try {
//       const response = await fetch(`https://f09b-194-58-154-209.ngrok-free.app/decks/${user.id}`, {
//         method: 'GET',
//         headers: { 'ngrok-skip-browser-warning': '69420' },
//       });
//       if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
//       const data = await response.json();
//       setDecks(data);
//     } catch (error) {
//       console.error('Error fetching decks:', error);
//     }
//   };
//
//   const createDeck = async () => {
//     if (!user?.id || !deckName.trim()) return;
//     if (isLanguageDeck && (!sourceLang || !targetLang)) {
//       alert('Выберите исходный и целевой языки для языковой колоды');
//       return;
//     }
//     const payload = {
//       telegram_id: user.id,
//       name: deckName.trim(),
//       is_language_deck: isLanguageDeck,
//       source_lang: isLanguageDeck ? sourceLang : null,
//       target_lang: isLanguageDeck ? targetLang : null,
//     };
//     try {
//       const response = await fetch('https://f09b-194-58-154-209.ngrok-free.app/decks/', {
//         method: 'POST',
//         headers: {
//           'Content-Type': 'application/json',
//           'ngrok-skip-browser-warning': '69420',
//         },
//         body: JSON.stringify(payload),
//       });
//       if (!response.ok) {
//         const errorData = await response.json();
//         throw new Error(`HTTP error! Status: ${response.status}, ${JSON.stringify(errorData)}`);
//       }
//       const newDeck = await response.json();
//       setDeckName('');
//       setIsLanguageDeck(false);
//       setSourceLang('');
//       setTargetLang('');
//       // Обновляем список колод
//       setDecks(prev => [...prev, newDeck]);
//       if (showDecks) await fetchDecks();
//     } catch (error) {
//       console.error('Error creating deck:', error);
//       alert(`Ошибка при создании колоды: ${error.message}`);
//     }
//   };
//
//   const handleShowDecks = async () => {
//     if (!showDecks) {
//       await fetchDecks();
//     }
//     setShowDecks(!showDecks);
//     setSelectedDeck(null);
//     setCards([]);
//     setShowCardModal(false);
//     setStudyMode(false);
//     setFinishedStudy(false);
//     setCorrectCount(0);
//     setIncorrectCount(0);
//     setCurrentCardIndex(0);
//     setIsFlipped(false);
//     setSwipeDirection(null);
//   };
//
//   const openAddCardsModal = async (deckId) => {
//     setSelectedDeck(deckId);
//     setShowCardModal(true);
//     try {
//       const deckResponse = await fetch(`https://f09b-194-58-154-209.ngrok-free.app/decks/${user.id}`, {
//         headers: { 'ngrok-skip-browser-warning': '69420' },
//       });
//       if (!deckResponse.ok) throw new Error(`HTTP error! Status: ${deckResponse.status}`);
//       const deckData = await deckResponse.json();
//       const deck = deckData.find(d => d.id === deckId);
//       setIsLanguageDeckSelected(deck.is_language_deck);
//
//       const endpoint = deck.is_language_deck ? `/lang_cards/${deckId}` : `/cards/${deckId}`;
//       const response = await fetch(`https://f09b-194-58-154-209.ngrok-free.app${endpoint}`, {
//         headers: { 'ngrok-skip-browser-warning': '69420' },
//       });
//       if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
//       const data = await response.json();
//       setCards(data);
//       setCardRows(data.map(card => (
//           deck.is_language_deck
//               ? { id: card.id, word: card.word, translation: card.translation }
//               : { id: card.id, term: card.term, definition: card.definition }
//       )));
//     } catch (error) {
//       console.error('Error fetching cards:', error);
//       setCardRows([]);
//     }
//   };
//
//   const startStudy = async (deckId) => {
//     setSelectedDeck(deckId);
//     setStudyMode(true);
//     setFinishedStudy(false);
//     setCorrectCount(0);
//     setIncorrectCount(0);
//     setCurrentCardIndex(0);
//     setIsFlipped(false);
//     setSwipeDirection(null);
//
//     try {
//       const deckResponse = await fetch(`https://f09b-194-58-154-209.ngrok-free.app/decks/${user.id}`, {
//         headers: { 'ngrok-skip-browser-warning': '69420' },
//       });
//       if (!deckResponse.ok) throw new Error(`HTTP error! Status: ${deckResponse.status}`);
//       const deckData = await deckResponse.json();
//       const deck = deckData.find(d => d.id === deckId);
//       setIsLanguageDeckSelected(deck.is_language_deck);
//
//       const endpoint = deck.is_language_deck ? `/lang_cards/${deckId}` : `/cards/${deckId}`;
//       const response = await fetch(`https://f09b-194-58-154-209.ngrok-free.app${endpoint}`, {
//         headers: { 'ngrok-skip-browser-warning': '69420' },
//       });
//       if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
//       const data = await response.json();
//       setCards(data.map(card => (
//           deck.is_language_deck
//               ? { id: card.id, term: card.word, definition: card.translation }
//               : card
//       )));
//     } catch (error) {
//       console.error('Error fetching cards:', error);
//       setCards([]);
//     }
//   };
//
//   const addNewCardRow = () => {
//     setCardRows([...cardRows, isLanguageDeckSelected ? { word: '' } : { term: '', definition: '' }]);
//   };
//
//   const updateCardRow = (index, field, value) => {
//     const updatedRows = [...cardRows];
//     updatedRows[index][field] = value;
//     setCardRows(updatedRows);
//   };
//
//   const removeCardRow = async (index) => {
//     const row = cardRows[index];
//     if (row.id) {
//       try {
//         const endpoint = isLanguageDeckSelected ? `/lang_cards/${row.id}` : `/cards/${row.id}`;
//         const response = await fetch(`https://f09b-194-58-154-209.ngrok-free.app${endpoint}`, {
//           method: 'DELETE',
//           headers: { 'ngrok-skip-browser-warning': '69420' },
//         });
//         if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
//         setCards(cards.filter(c => c.id !== row.id));
//       } catch (error) {
//         console.error('Error deleting card:', error);
//       }
//     }
//     setCardRows(cardRows.filter((_, i) => i !== index));
//   };
//
//   const saveCards = async () => {
//     if (!selectedDeck) return;
//     const newCards = cardRows.filter(row => !row.id && (isLanguageDeckSelected ? row.word.trim() : row.term.trim() && row.definition.trim()));
//     const updatedCards = cardRows.filter(row => row.id && (
//         isLanguageDeckSelected
//             ? row.word.trim() !== cards.find(c => c.id === row.id)?.word || row.translation.trim() !== cards.find(c => c.id === row.id)?.translation
//             : row.term.trim() !== cards.find(c => c.id === row.id)?.term || row.definition.trim() !== cards.find(c => c.id === row.id)?.definition
//     ));
//
//     try {
//       const deckResponse = await fetch(`https://f09b-194-58-154-209.ngrok-free.app/decks/${user.id}`, {
//         headers: { 'ngrok-skip-browser-warning': '69420' },
//       });
//       if (!deckResponse.ok) throw new Error(`HTTP error! Status: ${deckResponse.status}`);
//       const deckData = await deckResponse.json();
//       const deck = deckData.find(d => d.id === selectedDeck);
//
//       const endpoint = isLanguageDeckSelected ? '/lang_cards/' : '/cards/';
//       const createPromises = newCards.map(card =>
//           fetch(`https://f09b-194-58-154-209.ngrok-free.app${endpoint}`, {
//             method: 'POST',
//             headers: {
//               'Content-Type': 'application/json',
//               'ngrok-skip-browser-warning': '69420',
//             },
//             body: JSON.stringify(
//                 isLanguageDeckSelected
//                     ? {
//                       deck_id: selectedDeck,
//                       word: card.word.trim(),
//                       source_lang: deck.source_lang,
//                       target_lang: deck.target_lang,
//                     }
//                     : {
//                       deck_id: selectedDeck,
//                       term: card.term.trim(),
//                       definition: card.definition.trim(),
//                     }
//             ),
//           }).then(async response => {
//             if (!response.ok) {
//               const errorData = await response.json();
//               throw new Error(`HTTP error! Status: ${response.status}, ${JSON.stringify(errorData)}`);
//             }
//             return response.json();
//           })
//       );
//
//       const updatePromises = updatedCards.map(card =>
//           fetch(`https://f09b-194-58-154-209.ngrok-free.app${isLanguageDeckSelected ? '/lang_cards/' : '/cards/'}${card.id}`, {
//             method: 'PUT',
//             headers: {
//               'Content-Type': 'application/json',
//               'ngrok-skip-browser-warning': '69420',
//             },
//             body: JSON.stringify(
//                 isLanguageDeckSelected
//                     ? { word: card.word.trim(), translation: card.translation.trim() }
//                     : { term: card.term.trim(), definition: card.definition.trim() }
//             ),
//           }).then(async response => {
//             if (!response.ok) {
//               const errorData = await response.json();
//               throw new Error(`HTTP error! Status: ${response.status}, ${JSON.stringify(errorData)}`);
//             }
//             return response.json();
//           })
//       );
//
//       const [newCardsData, updatedCardsData] = await Promise.all([
//         Promise.all(createPromises),
//         Promise.all(updatePromises)
//       ]);
//
//       // Обновляем локальный стейт
//       setCards([
//         ...cards.filter(c => !updatedCards.some(uc => uc.id === c.id)),
//         ...newCardsData.map(card => (
//             isLanguageDeckSelected
//                 ? { id: card.id, word: card.word, translation: card.translation }
//                 : card
//         )),
//         ...updatedCardsData.map(card => (
//             isLanguageDeckSelected
//                 ? { id: card.id, word: card.word, translation: card.translation }
//                 : card
//         )),
//       ]);
//
//       setCardRows([]);
//       setShowCardModal(false);
//     } catch (error) {
//       console.error('Error saving cards:', error);
//     }
//   };
//
//   const closeModal = () => {
//     setShowCardModal(false);
//     setCardRows([]);
//   };
//
//   // Обработка свайпа: считаем правильные/неправильные и переключаемся на следующую карточку
//   const handleSwipe = (direction) => {
//     // Если это не последний индекс, считаем результат и переходим к следующей карточке
//     if (currentCardIndex < cards.length - 1) {
//       if (direction === 'right') {
//         setCorrectCount(prev => prev + 1);
//       } else if (direction === 'left') {
//         setIncorrectCount(prev => prev + 1);
//       }
//       setSwipeDirection(direction);
//       setTimeout(() => {
//         setCurrentCardIndex(prev => prev + 1);
//         setIsFlipped(false);
//         setSwipeDirection(null);
//       }, 300); // длительность анимации
//     } else {
//       // Последняя карточка
//       if (direction === 'right') {
//         setCorrectCount(prev => prev + 1);
//       } else if (direction === 'left') {
//         setIncorrectCount(prev => prev + 1);
//       }
//       setSwipeDirection(direction);
//       // После анимации показываем экран результатов
//       setTimeout(() => {
//         setFinishedStudy(true);
//       }, 300);
//     }
//   };
//
//   const swipeHandlers = useSwipeable({
//     onSwipedLeft: () => handleSwipe('left'),
//     onSwipedRight: () => handleSwipe('right'),
//     trackMouse: true,
//   });
//
//   const toggleFlip = () => {
//     setIsFlipped(prev => !prev);
//   };
//
//   const exitStudy = () => {
//     // Сброс всех состояний до основного экрана
//     setStudyMode(false);
//     setSelectedDeck(null);
//     setCards([]);
//     setCurrentCardIndex(0);
//     setIsFlipped(false);
//     setSwipeDirection(null);
//     setFinishedStudy(false);
//     setCorrectCount(0);
//     setIncorrectCount(0);
//   };
//
//   if (!user) {
//     return <p>Не удалось загрузить данные пользователя. Пожалуйста, перезапустите бота или проверьте настройки.</p>;
//   }
//
//   if (studyMode && finishedStudy) {
//     const total = cards.length;
//     const correctPercent = total > 0 ? Math.round((correctCount / total) * 100) : 0;
//
//     return (
//         <div className="App study">
//           <h1>Результаты изучения</h1>
//           <p>Всего карточек: <strong>{total}</strong></p>
//           <p>Запомнили: <strong>{correctCount}</strong></p>
//           <p>Не запомнили: <strong>{incorrectCount}</strong></p>
//           <p>Процент правильных: <strong>{correctPercent}%</strong></p>
//           <div className="study-buttons">
//             <button onClick={exitStudy}>Вернуться к списку колод</button>
//           </div>
//         </div>
//     );
//   }
//
//   if (studyMode && !finishedStudy) {
//     return (
//         <div className="App study">
//           <h1>Изучение карточек</h1>
//           <p className="card-counter">Карточка {currentCardIndex + 1} из {cards.length}</p>
//
//           {cards.length > 0 ? (
//               <div className="study-container" {...swipeHandlers}>
//                 <div
//                     className={`
//                 study-card
//                 ${isFlipped ? 'flipped' : ''}
//                 ${swipeDirection ? `swipe-${swipeDirection}` : ''}
//               `}
//                     onClick={toggleFlip}
//                 >
//                   <div className="card-front">
//                     <div className="card-content">
//                       <p>{cards[currentCardIndex].term}</p>
//                     </div>
//                   </div>
//                   <div className="card-back">
//                     <div className="card-content">
//                       <p>{cards[currentCardIndex].definition}</p>
//                     </div>
//                   </div>
//                 </div>
//               </div>
//           ) : (
//               <p>Добавьте карточки, чтобы начать изучение.</p>
//           )}
//
//           <p>Свайп влево — не запомнил, вправо — запомнил.</p>
//           <div className="study-buttons">
//             <button onClick={exitStudy}>Завершить</button>
//           </div>
//         </div>
//     );
//   }
//
//   // Основной экран (без режима изучения)
//   return (
//       <div className="App">
//         <h1>Flashcards Mini App</h1>
//         <p>Привет!</p>
//
//         <div className="create-deck">
//           <input
//               type="text"
//               value={deckName}
//               onChange={(e) => setDeckName(e.target.value)}
//               placeholder="Название колоды"
//           />
//           <label style={{display: 'inline-flex', alignItems: 'center', gap: '5px'}}>
//             <input
//                 type="checkbox"
//                 checked={isLanguageDeck}
//                 onChange={(e) => setIsLanguageDeck(e.target.checked)}
//             />
//             🌐
//           </label>
//           {isLanguageDeck && (
//               <div className="language-select" style={{ marginTop: '10px' }}>
//                 <select
//                     value={sourceLang}
//                     onChange={(e) => setSourceLang(e.target.value)}
//                     required
//                 >
//                   <option value="">исходный язык</option>
//                   {languages.map(lang => (
//                       <option key={lang.code} value={lang.code}>{lang.name}</option>
//                   ))}
//                 </select>
//                 <select
//                     value={targetLang}
//                     onChange={(e) => setTargetLang(e.target.value)}
//                     required
//                 >
//                   <option value="">целевой язык</option>
//                   {languages.map(lang => (
//                       <option key={lang.code} value={lang.code}>{lang.name}</option>
//                   ))}
//                 </select>
//               </div>
//           )}
//           <button onClick={createDeck} style={{ marginTop: '15px' }}>Создать колоду</button>
//         </div>
//
//         <div>
//           <button className="toggle-decks-button" onClick={handleShowDecks}>
//             {showDecks ? 'Скрыть колоды' : 'Мои колоды'}
//           </button>
//         </div>
//
//         {showDecks && (
//             <div className="decks-container">
//               <h2>Ваши колоды:</h2>
//               <ul>
//                 {decks.length > 0 ? (
//                     decks.map((deck) => (
//                         <li key={deck.id} className="deck-item">
//                           <span>{deck.name} {deck.is_language_deck ? '🌐' : ''}</span>
//                           <div className="deck-actions">
//                             <button
//                                 className="add-cards-button"
//                                 onClick={() => openAddCardsModal(deck.id)}
//                             >
//                               Карточки
//                             </button>
//                             <button
//                                 className="study-button"
//                                 onClick={() => startStudy(deck.id)}
//                             >
//                               Изучить
//                             </button>
//                           </div>
//                         </li>
//                     ))
//                 ) : (
//                     <p>У вас пока нет колод.</p>
//                 )}
//               </ul>
//             </div>
//         )}
//
//         {showCardModal && selectedDeck && (
//             <div className="modal">
//               <div className="modal-content">
//                 <h2>Редактировать карточки</h2>
//                 <div className="card-form">
//                   {cardRows.map((row, index) => (
//                       <div key={row.id || `new-${index}`} className="card-row">
//                         {isLanguageDeckSelected ? (
//                             <input
//                                 type="text"
//                                 value={row.word}
//                                 onChange={(e) => updateCardRow(index, 'word', e.target.value)}
//                                 placeholder="Слово"
//                             />
//                         ) : (
//                             <>
//                               <input
//                                   type="text"
//                                   value={row.term}
//                                   onChange={(e) => updateCardRow(index, 'term', e.target.value)}
//                                   placeholder="Термин"
//                               />
//                               <textarea
//                                   value={row.definition}
//                                   onChange={(e) => updateCardRow(index, 'definition', e.target.value)}
//                                   placeholder="Определение"
//                                   rows="3"
//                               />
//                             </>
//                         )}
//                         <button className="remove-row" onClick={() => removeCardRow(index)}>×</button>
//                       </div>
//                   ))}
//                   <button className="add-row" onClick={addNewCardRow}>+</button>
//                   <div className="modal-buttons">
//                     <button onClick={saveCards}>Сохранить</button>
//                     <button onClick={closeModal}>Закрыть</button>
//                   </div>
//                 </div>
//               </div>
//             </div>
//         )}
//       </div>
//   );
// }
//
// export default App;

import {useEffect, useRef, useState} from 'react';
import TelegramWebApp from '@twa-dev/sdk';
import { useSwipeable } from 'react-swipeable';
import './App.css';

function App() {
  const [user, setUser] = useState(null);
  const [decks, setDecks] = useState([]);
  const [deckName, setDeckName] = useState('');
  const [showDecks, setShowDecks] = useState(false);
  const [selectedDeck, setSelectedDeck] = useState(null);
  const [cards, setCards] = useState([]);
  const [showCardModal, setShowCardModal] = useState(false);
  const [cardRows, setCardRows] = useState([]);
  const [studyMode, setStudyMode] = useState(false);
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [swipeDirection, setSwipeDirection] = useState(null);
  const [correctCount, setCorrectCount] = useState(0);
  const [incorrectCount, setIncorrectCount] = useState(0);
  const [finishedStudy, setFinishedStudy] = useState(false);
  const [isLanguageDeck, setIsLanguageDeck] = useState(false);
  const [sourceLang, setSourceLang] = useState('');
  const [targetLang, setTargetLang] = useState('');
  const [languages, setLanguages] = useState([]);
  const [isLanguageDeckSelected, setIsLanguageDeckSelected] = useState(false);
  const [translatingRows, setTranslatingRows] = useState({}); // Индикатор загрузки для каждой строки

  const NGROK_URL = 'https://f09b-194-58-154-209.ngrok-free.app';
  const debounceTimeout = useRef(null);
  const lastTranslatedWords = useRef({});

  const fetchUserInfo = async (telegramId) => {
    try {
      const response = await fetch(`${NGROK_URL}/user/${telegramId}/`, {
        headers: { 'ngrok-skip-browser-warning': '69420' },
      });
      if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error('Error fetching user info:', error);
      return { id: telegramId, first_name: 'Guest' };
    }
  };

  const fetchLanguages = async () => {
    try {
      const response = await fetch(`${NGROK_URL}/languages/`, {
        headers: { 'ngrok-skip-browser-warning': '69420' },
      });
      if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
      const data = await response.json();
      setLanguages(data);
    } catch (error) {
      console.error('Error fetching languages:', error);
    }
  };

  const fetchTranslation = async (word, sourceLang, targetLang, rowIndex) => {
    console.log('Translating:', { word, sourceLang, targetLang, rowIndex });
    if (!word.trim() || !sourceLang || !targetLang || word.trim().length < 2) {
      setTranslatingRows(prev => ({ ...prev, [rowIndex]: false }));
      return '';
    }
    // Проверяем, не переводили ли это слово недавно
    if (lastTranslatedWords.current[rowIndex] === word.trim()) {
      setTranslatingRows(prev => ({ ...prev, [rowIndex]: false }));
      return cardRows[rowIndex].translation || '';
    }
    setTranslatingRows(prev => ({ ...prev, [rowIndex]: true }));
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);
      const response = await fetch(`${NGROK_URL}/translate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'ngrok-skip-browser-warning': '69420' },
        body: JSON.stringify({
          q: word.trim(),
          source: sourceLang,
          target: targetLang,
          format: 'text',
        }),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(`Translation failed: ${response.status} - ${errorData.detail || 'Unknown error'}`);
      }
      const data = await response.json();
      console.log('Translation response:', data);
      if (!data.translatedText) throw new Error('No translated text in response');
      lastTranslatedWords.current[rowIndex] = word.trim(); // Сохраняем переведённое слово
      return data.translatedText;
    } catch (error) {
      console.error('Error fetching translation:', { word, sourceLang, targetLang, error: error.message });
      return `Ошибка перевода: ${error.message}`;
    } finally {
      setTranslatingRows(prev => ({ ...prev, [rowIndex]: false }));
    }
  };

  useEffect(() => {
    TelegramWebApp.ready();
    const initData = TelegramWebApp.initDataUnsafe;

    const setUserData = async () => {
      if (initData && initData.user) {
        setUser(initData.user);
      } else {
        const urlParams = new URLSearchParams(window.location.search);
        const telegramIdFromUrl = urlParams.get('telegram_id');
        if (telegramIdFromUrl) {
          const telegramId = parseInt(telegramIdFromUrl);
          const userInfo = await fetchUserInfo(telegramId);
          setUser(userInfo);
        } else {
          console.error('No user data in initData or URL');
        }
      }
    };

    setUserData();
    fetchLanguages();
  }, []);

  useEffect(() => {
    if (!isLanguageDeckSelected || cardRows.length === 0 || !selectedDeck) return;

    if (debounceTimeout.current) {
      clearTimeout(debounceTimeout.current);
    }

    debounceTimeout.current = setTimeout(async () => {
      const deck = decks.find(d => d.id === selectedDeck);
      if (!deck || !deck.source_lang || !deck.target_lang) return;

      let hasChanges = false;
      const updatedRows = [...cardRows]; // Копируем, чтобы избежать прямого мутирования

      for (let index = 0; index < cardRows.length; index++) {
        const row = cardRows[index];
        const currentCard = cards.find(c => c.id === row.id);
        const needsTranslation =
            row.word.trim().length >= 2 &&
            !translatingRows[index] &&
            (!row.translation ||
                (currentCard && row.word.trim() !== currentCard.word) ||
                row.translation.startsWith('Ошибка перевода'));

        if (needsTranslation) {
          const translation = await fetchTranslation(
              row.word,
              deck.source_lang,
              deck.target_lang,
              index
          );
          if (translation && !translation.startsWith('Ошибка перевода')) {
            updatedRows[index] = { ...row, translation };
            hasChanges = true;
          }
        }
      }

      if (hasChanges) {
        setCardRows(updatedRows);
      }
    }, 500);

    return () => clearTimeout(debounceTimeout.current);
  }, [cardRows, isLanguageDeckSelected, selectedDeck, decks, translatingRows, cards]);

  const fetchDecks = async () => {
    if (!user?.id) return;
    try {
      const response = await fetch(`${NGROK_URL}/decks/${user.id}`, {
        headers: { 'ngrok-skip-browser-warning': '69420' },
      });
      if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
      const data = await response.json();
      setDecks(data);
    } catch (error) {
      console.error('Error fetching decks:', error);
    }
  };

  const createDeck = async () => {
    if (!user?.id || !deckName.trim()) {
      alert('Введите название колоды');
      return;
    }
    if (isLanguageDeck && (!sourceLang || !targetLang)) {
      alert('Выберите исходный и целевой языки для языковой колоды');
      return;
    }
    const payload = {
      telegram_id: user.id,
      name: deckName.trim(),
      is_language_deck: isLanguageDeck,
      source_lang: isLanguageDeck ? sourceLang : null,
      target_lang: isLanguageDeck ? targetLang : null,
    };
    try {
      const response = await fetch(`${NGROK_URL}/decks/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'ngrok-skip-browser-warning': '69420',
        },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`Ошибка: ${JSON.stringify(errorData)}`);
      }
      const newDeck = await response.json();
      setDeckName('');
      setIsLanguageDeck(false);
      setSourceLang('');
      setTargetLang('');
      setDecks(prev => [...prev, newDeck]);
      if (showDecks) await fetchDecks();
    } catch (error) {
      console.error('Error creating deck:', error);
      alert(`Ошибка при создании колоды: ${error.message}`);
    }
  };

  const handleShowDecks = async () => {
    if (!showDecks) await fetchDecks();
    setShowDecks(!showDecks);
    setSelectedDeck(null);
    setCards([]);
    setShowCardModal(false);
    setStudyMode(false);
    setFinishedStudy(false);
    setCorrectCount(0);
    setIncorrectCount(0);
    setCurrentCardIndex(0);
    setIsFlipped(false);
    setSwipeDirection(null);
  };

  const openAddCardsModal = async (deckId) => {
    setSelectedDeck(deckId);
    setShowCardModal(true);
    try {
      const deckResponse = await fetch(`${NGROK_URL}/decks/${user.id}`, {
        headers: { 'ngrok-skip-browser-warning': '69420' },
      });
      if (!deckResponse.ok) throw new Error(`HTTP error! Status: ${deckResponse.status}`);
      const deckData = await deckResponse.json();
      const deck = deckData.find(d => d.id === deckId);
      setIsLanguageDeckSelected(deck.is_language_deck);

      const endpoint = deck.is_language_deck ? `/lang_cards/${deckId}` : `/cards/${deckId}`;
      const response = await fetch(`${NGROK_URL}${endpoint}`, {
        headers: { 'ngrok-skip-browser-warning': '69420' },
      });
      if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
      const data = await response.json();
      setCards(data);
      setCardRows(data.map(card => (
          deck.is_language_deck
              ? { id: card.id, word: card.word, translation: card.translation || '' }
              : { id: card.id, term: card.term, definition: card.definition }
      )));
    } catch (error) {
      console.error('Error fetching cards:', error);
      setCardRows([]);
    }
  };

  const startStudy = async (deckId) => {
    setSelectedDeck(deckId);
    setStudyMode(true);
    setFinishedStudy(false);
    setCorrectCount(0);
    setIncorrectCount(0);
    setCurrentCardIndex(0);
    setIsFlipped(false);
    setSwipeDirection(null);
    try {
      const deckResponse = await fetch(`${NGROK_URL}/decks/${user.id}`, {
        headers: { 'ngrok-skip-browser-warning': '69420' },
      });
      if (!deckResponse.ok) throw new Error(`HTTP error! Status: ${deckResponse.status}`);
      const deckData = await deckResponse.json();
      const deck = deckData.find(d => d.id === deckId);
      setIsLanguageDeckSelected(deck.is_language_deck);
      const endpoint = deck.is_language_deck ? `/lang_cards/${deckId}` : `/cards/${deckId}`;
      const response = await fetch(`${NGROK_URL}${endpoint}`, {
        headers: { 'ngrok-skip-browser-warning': '69420' },
      });
      if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
      const data = await response.json();
      setCards(data.map(card => (
          deck.is_language_deck
              ? { id: card.id, term: card.word, definition: card.translation }
              : card
      )));
    } catch (error) {
      console.error('Error fetching cards:', error);
      setCards([]);
    }
  };

  const addNewCardRow = () => {
    const newRow = isLanguageDeckSelected
        ? { word: '', translation: '' }
        : { term: '', definition: '' };
    setCardRows(prev => [...prev, newRow]);
  };

  const updateCardRow = (index, field, value) => {
    const updatedRows = [...cardRows];
    updatedRows[index] = { ...updatedRows[index], [field]: value };
    setCardRows(updatedRows);
  };

  const removeCardRow = async (index) => {
    const row = cardRows[index];
    if (row.id) {
      try {
        const endpoint = isLanguageDeckSelected ? `/lang_cards/${row.id}` : `/cards/${row.id}`;
        const response = await fetch(`${NGROK_URL}${endpoint}`, {
          method: 'DELETE',
          headers: { 'ngrok-skip-browser-warning': '69420' },
        });
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
        setCards(cards.filter(c => c.id !== row.id));
      } catch (error) {
        console.error('Error deleting card:', error);
      }
    }
    setCardRows(cardRows.filter((_, i) => i !== index));
    setTranslatingRows(prev => {
      const newState = { ...prev };
      delete newState[index];
      return newState;
    });
  };

  const saveCards = async () => {
    if (!selectedDeck) return;
    const deck = decks.find(d => d.id === selectedDeck);
    if (!deck) return;

    // Проверка на пустые поля
    const invalidRows = cardRows.filter(row => (
        isLanguageDeckSelected
            ? !row.word.trim() || !row.translation?.trim()
            : !row.term.trim() || !row.definition.trim()
    ));
    if (invalidRows.length > 0) {
      alert('Заполните все поля для новых карточек (слово и перевод или термин и определение).');
      return;
    }

    const newCards = cardRows.filter(row => !row.id);
    const updatedCards = cardRows.filter(row => row.id && (
        isLanguageDeckSelected
            ? row.word.trim() !== cards.find(c => c.id === row.id)?.word || row.translation?.trim() !== cards.find(c => c.id === row.id)?.translation
            : row.term.trim() !== cards.find(c => c.id === row.id)?.term || row.definition.trim() !== cards.find(c => c.id === row.id)?.definition
    ));

    try {
      const endpoint = isLanguageDeckSelected ? '/lang_cards/' : '/cards/';
      const createPromises = newCards.map(card =>
          fetch(`${NGROK_URL}${endpoint}`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'ngrok-skip-browser-warning': '69420',
            },
            body: JSON.stringify(
                isLanguageDeckSelected
                    ? {
                      deck_id: selectedDeck,
                      word: card.word.trim(),
                      source_lang: deck.source_lang,
                      target_lang: deck.target_lang,
                      translation: card.translation?.trim() || null
                    }
                    : {
                      deck_id: selectedDeck,
                      term: card.term.trim(),
                      definition: card.definition.trim(),
                    }
            ),
          }).then(async response => {
            if (!response.ok) {
              const errorData = await response.json();
              throw new Error(`Ошибка: ${JSON.stringify(errorData)}`);
            }
            return response.json();
          })
      );

      const updatePromises = updatedCards.map(card =>
          fetch(`${NGROK_URL}${isLanguageDeckSelected ? '/lang_cards/' : '/cards/'}${card.id}`, {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
              'ngrok-skip-browser-warning': '69420',
            },
            body: JSON.stringify(
                isLanguageDeckSelected
                    ? { word: card.word.trim(), translation: card.translation?.trim() || '' }
                    : { term: card.term.trim(), definition: card.definition.trim() }
            ),
          }).then(async response => {
            if (!response.ok) {
              const errorData = await response.json();
              throw new Error(`Ошибка: ${JSON.stringify(errorData)}`);
            }
            return response.json();
          })
      );

      const [newCardsData, updatedCardsData] = await Promise.all([
        Promise.all(createPromises),
        Promise.all(updatePromises)
      ]);

      setCards([
        ...cards.filter(c => !updatedCards.some(uc => uc.id === c.id)),
        ...newCardsData.map(card => (
            isLanguageDeckSelected
                ? { id: card.id, word: card.word, translation: card.translation }
                : card
        )),
        ...updatedCardsData.map(card => (
            isLanguageDeckSelected
                ? { id: card.id, word: card.word, translation: card.translation }
                : card
        )),
      ]);

      setCardRows([]);
      setShowCardModal(false);
      setTranslatingRows({});
      alert('Карточки успешно сохранены!');
    } catch (error) {
      console.error('Error saving cards:', error);
      alert(`Ошибка при сохранении карточек: ${error.message}`);
    }
  };

  const closeModal = () => {
    setShowCardModal(false);
    setCardRows([]);
    setTranslatingRows({});
  };

  const handleSwipe = (direction) => {
    if (currentCardIndex < cards.length - 1) {
      if (direction === 'right') setCorrectCount(prev => prev + 1);
      else if (direction === 'left') setIncorrectCount(prev => prev + 1);
      setSwipeDirection(direction);
      setTimeout(() => {
        setCurrentCardIndex(prev => prev + 1);
        setIsFlipped(false);
        setSwipeDirection(null);
      }, 300);
    } else {
      if (direction === 'right') setCorrectCount(prev => prev + 1);
      else if (direction === 'left') setIncorrectCount(prev => prev + 1);
      setSwipeDirection(direction);
      setTimeout(() => setFinishedStudy(true), 300);
    }
  };

  const swipeHandlers = useSwipeable({
    onSwipedLeft: () => handleSwipe('left'),
    onSwipedRight: () => handleSwipe('right'),
    trackMouse: true,
  });

  const toggleFlip = () => setIsFlipped(prev => !prev);

  const exitStudy = () => {
    setStudyMode(false);
    setSelectedDeck(null);
    setCards([]);
    setCurrentCardIndex(0);
    setIsFlipped(false);
    setSwipeDirection(null);
    setFinishedStudy(false);
    setCorrectCount(0);
    setIncorrectCount(0);
  };

  if (!user) {
    return <p>Не удалось загрузить данные пользователя. Пожалуйста, перезапустите бота или проверьте настройки.</p>;
  }

  if (studyMode && finishedStudy) {
    const total = cards.length;
    const correctPercent = total > 0 ? Math.round((correctCount / total) * 100) : 0;
    return (
        <div className="App study">
          <h1>Результаты изучения</h1>
          <p>Всего карточек: <strong>{total}</strong></p>
          <p>Запомнили: <strong>{correctCount}</strong></p>
          <p>Не запомнили: <strong>{incorrectCount}</strong></p>
          <p>Процент правильных: <strong>{correctPercent}%</strong></p>
          <div className="study-buttons">
            <button onClick={exitStudy}>Вернуться к списку колод</button>
          </div>
        </div>
    );
  }

  if (studyMode && !finishedStudy) {
    return (
        <div className="App study">
          <h1>Изучение карточек</h1>
          <p className="card-counter">Карточка {currentCardIndex + 1} из {cards.length}</p>
          {cards.length > 0 ? (
              <div className="study-container" {...swipeHandlers}>
                <div
                    className={`
                study-card
                ${isFlipped ? 'flipped' : ''}
                ${swipeDirection ? `swipe-${swipeDirection}` : ''}
              `}
                    onClick={toggleFlip}
                >
                  <div className="card-front">
                    <div className="card-content">
                      <p>{cards[currentCardIndex].term}</p>
                    </div>
                  </div>
                  <div className="card-back">
                    <div className="card-content">
                      <p>{cards[currentCardIndex].definition}</p>
                    </div>
                  </div>
                </div>
              </div>
          ) : (
              <p>Добавьте карточки, чтобы начать изучение.</p>
          )}
          <p>Свайп влево — не запомнил, вправо — запомнил.</p>
          <div className="study-buttons">
            <button onClick={exitStudy}>Завершить</button>
          </div>
        </div>
    );
  }

  return (
      <div className="App">
        <h1>Flashcards Mini App</h1>
        <p>Привет!</p>
        <div className="create-deck">
          <input
              type="text"
              value={deckName}
              onChange={(e) => setDeckName(e.target.value)}
              placeholder="Название колоды"
          />
          <label style={{ display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
            <input
                type="checkbox"
                checked={isLanguageDeck}
                onChange={(e) => setIsLanguageDeck(e.target.checked)}
            />
            🌐
          </label>
          {isLanguageDeck && (
              <div className="language-select">
                <select
                    value={sourceLang}
                    onChange={(e) => setSourceLang(e.target.value)}
                    required
                >
                  <option value="">исходный язык</option>
                  {languages.map(lang => (
                      <option key={lang.code} value={lang.code}>{lang.name}</option>
                  ))}
                </select>
                <select
                    value={targetLang}
                    onChange={(e) => setTargetLang(e.target.value)}
                    required
                >
                  <option value="">целевой язык</option>
                  {languages.map(lang => (
                      <option key={lang.code} value={lang.code}>{lang.name}</option>
                  ))}
                </select>
              </div>
          )}
          <button onClick={createDeck}>Создать колоду</button>
        </div>
        <div>
          <button className="toggle-decks-button" onClick={handleShowDecks}>
            {showDecks ? 'Скрыть колоды' : 'Мои колоды'}
          </button>
        </div>
        {showDecks && (
            <div className="decks-container">
              <h2>Ваши колоды:</h2>
              <ul>
                {decks.length > 0 ? (
                    decks.map((deck) => (
                        <li key={deck.id} className="deck-item">
                          <span>{deck.name} {deck.is_language_deck ? '🌐' : ''}</span>
                          <div className="deck-actions">
                            <button
                                className="add-cards-button"
                                onClick={() => openAddCardsModal(deck.id)}
                            >
                              Карточки
                            </button>
                            <button
                                className="study-button"
                                onClick={() => startStudy(deck.id)}
                            >
                              Изучить
                            </button>
                          </div>
                        </li>
                    ))
                ) : (
                    <p>У вас пока нет колод.</p>
                )}
              </ul>
            </div>
        )}
        {showCardModal && selectedDeck && (
            <div className="modal">
              <div className="modal-content">
                <h2>Редактировать карточки</h2>
                <div className="card-form">
                  {cardRows.map((row, index) => (
                      <div key={row.id || `new-${index}`} className="card-row">
                        {isLanguageDeckSelected ? (
                            <>
                              <input
                                  type="text"
                                  value={row.word}
                                  onChange={(e) => updateCardRow(index, 'word', e.target.value)}
                                  placeholder="Слово"
                              />
                              <div className="translation-container">
                                <input
                                    type="text"
                                    value={translatingRows[index] ? row.translation || '' : (row.translation || '')}
                                    onChange={(e) => updateCardRow(index, 'translation', e.target.value)}
                                    placeholder={translatingRows[index] ? 'Перевод...' : 'Перевод'}
                                    disabled={translatingRows[index]}
                                />
                                {translatingRows[index] && <span className="loading">...</span>}
                              </div>
                            </>
                        ) : (
                            <>
                              <input
                                  type="text"
                                  value={row.term}
                                  onChange={(e) => updateCardRow(index, 'term', e.target.value)}
                                  placeholder="Термин"
                              />
                              <textarea
                                  value={row.definition}
                                  onChange={(e) => updateCardRow(index, 'definition', e.target.value)}
                                  placeholder="Определение"
                                  rows="3"
                              />
                            </>
                        )}
                        <button className="remove-row" onClick={() => removeCardRow(index)}>×</button>
                      </div>
                  ))}
                  <button className="add-row" onClick={addNewCardRow}>+</button>
                  <div className="modal-buttons">
                    <button onClick={saveCards}>Сохранить</button>
                    <button onClick={closeModal}>Закрыть</button>
                  </div>
                </div>
              </div>
            </div>
        )}
      </div>
  );
}

export default App;
