pragma solidity ^0.4.18;



contract Bollette{

	mapping (bytes32 => uint32) public kwh_emessi;
	mapping (bytes32 => uint32) public importo_dovuto;
	mapping (bytes32 => address) public indirizzo;
	mapping (bytes32 => bool) public pagata;
	bytes32[] public lista_identificativi;
    address public owner;


	constructor() public {
	    owner = msg.sender;
	}



	function Emetti_Bolletta(bytes32 identificativo,uint32 kwh, uint32 cambio, address addr) public {
	    require(msg.sender==owner);
		require(!bill_exists(identificativo));
		kwh_emessi[identificativo] = kwh;
		importo_dovuto[identificativo] = kwh*cambio;
		pagata[identificativo] = false;
		indirizzo[identificativo] = addr;
		lista_identificativi.push(identificativo);
	}



	function Paga_Bollette(bytes32 identificativo) payable public {
	    require(indirizzo[identificativo]==msg.sender);
		require(bill_exists(identificativo));
		require(!pagata[identificativo]);
		require(msg.value==importo_dovuto[identificativo]);
		pagata[identificativo] = true;
		owner.transfer(msg.value);
	}

	

	function bill_exists(bytes32 identificativo) private constant returns(bool) {
		for (uint256 i=0; i<lista_identificativi.length;i++){
			if (lista_identificativi[i]==identificativo)
				return true;
		}
		return false;
	}
}
