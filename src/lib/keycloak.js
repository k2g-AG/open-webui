import Keycloak from 'keycloak-js';

const keycloak = new Keycloak({
	url: 'https://kck-box-dev.k2g.ai/realms/openweb-ui/protocol/openid-connect/auth',
	realm: 'openweb-ui',
	clientId: 'openweb-ui'
});

export default keycloak;
