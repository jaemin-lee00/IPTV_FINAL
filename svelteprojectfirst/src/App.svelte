<script>
	import Welcome from './Welcome.svelte';
	import InfoInput from './InfoInput.svelte';
	import InfoConfirm from './InfoConfirm.svelte';

	let currentPage = 'welcome';
	let userInfo = {};

	function startInfoInput() {
			currentPage = 'infoInput';
	}

	function finishInfoInput(event) {
			userInfo = event.detail;
			currentPage = 'infoConfirm';
	}

	function goBack() {
			if (currentPage === 'infoConfirm') {
					currentPage = 'infoInput';
			}
	}

	function goToWelcome() {
			currentPage = 'welcome';
	}
</script>

<main>
	{#if currentPage === 'welcome'}
			<Welcome on:start={startInfoInput} />
	{:else if currentPage === 'infoInput'}
			<InfoInput on:finish={finishInfoInput} on:goToWelcome={goToWelcome} />
	{:else if currentPage === 'infoConfirm'}
			<InfoConfirm {userInfo} on:back={goBack} />
	{/if}
</main>

<style>
	main {
			text-align: center;
			padding: 1em;
			max-width: 240px;
			margin: 0 auto;
	}

	@media (min-width: 640px) {
			main {
					max-width: none;
			}
	}
</style>
