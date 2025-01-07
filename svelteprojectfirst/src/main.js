import App from './App.svelte';

const app = new App({
	target: document.body,
	props: {
		name: '사용자'
	}
});

export default app;