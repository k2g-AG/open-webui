import Keycloak from 'keycloak-js';

const keycloak = new Keycloak({
	url: 'https://kck-box-dev.k2g.ai',
	realm: 'openweb-ui',
	clientId: 'openweb-ui'
});

export default keycloak;
