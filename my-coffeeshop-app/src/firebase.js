import { initializeApp } from 'firebase/app';

const firebaseConfig = {
    apiKey: "AIzaSyCvIDqbUMswOpiUuhK4T5F1xDtV6TF3DhY",
    authDomain: "esd-coffeehouse.firebaseapp.com",
    projectId: "esd-coffeehouse",
    storageBucket: "esd-coffeehouse.firebasestorage.app",
    messagingSenderId: "775228208734",
    appId: "1:775228208734:web:e789da4fb8fd39b6d6e6cf",
    measurementId: "G-6Q5J1S1KLP"
};

const app = initializeApp(firebaseConfig);

export default app;