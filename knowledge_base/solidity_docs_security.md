Security Considerations
While it is usually quite easy to build software that works as expected, it is much harder to check that nobody can use it in a way that was not anticipated.

In Solidity, this is even more important because you can use smart contracts to handle tokens or, possibly, even more valuable things. Furthermore, every execution of a smart contract happens in public and, in addition to that, the source code is often available.

Of course, you always have to consider how much is at stake: You can compare a smart contract with a web service that is open to the public (and thus, also to malicious actors) and perhaps even open-source. If you only store your grocery list on that web service, you might not have to take too much care, but if you manage your bank account using that web service, you should be more careful.

This section will list some pitfalls and general security recommendations but can, of course, never be complete. Also, keep in mind that even if your smart contract code is bug-free, the compiler or the platform itself might have a bug. A list of some publicly known security-relevant bugs of the compiler can be found in the list of known bugs, which is also machine-readable. Note that there is a Bug Bounty Program that covers the code generator of the Solidity compiler.

As always, with open-source documentation, please help us extend this section (especially, some examples would not hurt)!

NOTE: In addition to the list below, you can find more security recommendations and best practices in Guy Lando’s knowledge list and the Consensys GitHub repo.

Pitfalls
Private Information and Randomness
Everything you use in a smart contract is publicly visible, even local variables and state variables marked private.

Using random numbers in smart contracts is quite tricky if you do not want block builders to be able to cheat.

Reentrancy
Any interaction from a contract (A) with another contract (B) and any transfer of Ether hands over control to that contract (B). This makes it possible for B to call back into A before this interaction is completed. To give an example, the following code contains a bug (it is just a snippet and not a complete contract):

open in Remix

// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.6.0 <0.9.0;

// THIS CONTRACT CONTAINS A BUG - DO NOT USE
contract Fund {
    /// @dev Mapping of ether shares of the contract.
    mapping(address => uint) shares;
    /// Withdraw your share.
    function withdraw() public {
        if (payable(msg.sender).send(shares[msg.sender]))
            shares[msg.sender] = 0;
    }
}
The problem is not too serious here because of the limited gas as part of send, but it still exposes a weakness: Ether transfer can always include code execution, so the recipient could be a contract that calls back into withdraw. This would let it get multiple refunds and, basically, retrieve all the Ether in the contract. In particular, the following contract will allow an attacker to refund multiple times as it uses call which forwards all remaining gas by default:

open in Remix

// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.6.2 <0.9.0;

// THIS CONTRACT CONTAINS A BUG - DO NOT USE
contract Fund {
    /// @dev Mapping of ether shares of the contract.
    mapping(address => uint) shares;
    /// Withdraw your share.
    function withdraw() public {
        (bool success,) = msg.sender.call{value: shares[msg.sender]}("");
        if (success)
            shares[msg.sender] = 0;
    }
}
To avoid reentrancy, you can use the Checks-Effects-Interactions pattern as demonstrated below:

open in Remix

// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.6.0 <0.9.0;

contract Fund {
    /// @dev Mapping of ether shares of the contract.
    mapping(address => uint) shares;
    /// Withdraw your share.
    function withdraw() public {
        uint share = shares[msg.sender];
        shares[msg.sender] = 0;
        payable(msg.sender).transfer(share);
    }
}
The Checks-Effects-Interactions pattern ensures that all code paths through a contract complete all required checks of the supplied parameters before modifying the contract’s state (Checks); only then it makes any changes to the state (Effects); it may make calls to functions in other contracts after all planned state changes have been written to storage (Interactions). This is a common foolproof way to prevent reentrancy attacks, where an externally called malicious contract can double-spend an allowance, double-withdraw a balance, among other things, by using logic that calls back into the original contract before it has finalized its transaction.

Note that reentrancy is not only an effect of Ether transfer but of any function call on another contract. Furthermore, you also have to take multi-contract situations into account. A called contract could modify the state of another contract you depend on.

Gas Limit and Loops
Loops that do not have a fixed number of iterations, for example, loops that depend on storage values, have to be used carefully: Due to the block gas limit, transactions can only consume a certain amount of gas. Either explicitly or just due to normal operation, the number of iterations in a loop can grow beyond the block gas limit which can cause the complete contract to be stalled at a certain point. This may not apply to view functions that are only executed to read data from the blockchain. Still, such functions may be called by other contracts as part of on-chain operations and stall those. Please be explicit about such cases in the documentation of your contracts.

Sending and Receiving Ether
Neither contracts nor “externally-owned accounts” are currently able to prevent someone from sending them Ether. Contracts can react on and reject a regular transfer, but there are ways to move Ether without creating a message call. One way is to simply “mine to” the contract address and the second way is using selfdestruct(x).

If a contract receives Ether (without a function being called), either the receive Ether or the fallback function is executed. If it does not have a receive nor a fallback function, the Ether will be rejected (by throwing an exception). During the execution of one of these functions, the contract can only rely on the “gas stipend” it is passed (2300 gas) being available to it at that time. This stipend is not enough to modify storage (do not take this for granted though, the stipend might change with future hard forks). To be sure that your contract can receive Ether in that way, check the gas requirements of the receive and fallback functions (for example in the “details” section in Remix).

There is a way to forward more gas to the receiving contract using addr.call{value: x}(""). This is essentially the same as addr.transfer(x), only that it forwards all remaining gas and opens up the ability for the recipient to perform more expensive actions (and it returns a failure code instead of automatically propagating the error). This might include calling back into the sending contract or other state changes you might not have thought of. So it allows for great flexibility for honest users but also for malicious actors.

Use the most precise units to represent the Wei amount as possible, as you lose any that is rounded due to a lack of precision.

If you want to send Ether using address.transfer, there are certain details to be aware of:

If the recipient is a contract, it causes its receive or fallback function to be executed which can, in turn, call back the sending contract.

Sending Ether can fail due to the call depth going above 1024. Since the caller is in total control of the call depth, they can force the transfer to fail; take this possibility into account or use send and make sure to always check its return value. Better yet, write your contract using a pattern where the recipient can withdraw Ether instead.

Sending Ether can also fail because the execution of the recipient contract requires more than the allotted amount of gas (explicitly by using require, assert, revert or because the operation is too expensive) - it “runs out of gas” (OOG). If you use transfer or send with a return value check, this might provide a means for the recipient to block progress in the sending contract. Again, the best practice here is to use a “withdraw” pattern instead of a “send” pattern.

Call Stack Depth
External function calls can fail at any time because they exceed the maximum call stack size limit of 1024. In such situations, Solidity throws an exception. Malicious actors might be able to force the call stack to a high value before they interact with your contract. Note that, since Tangerine Whistle hardfork, the 63/64 rule makes call stack depth attack impractical. Also note that the call stack and the expression stack are unrelated, even though both have a size limit of 1024 stack slots.

Note that .send() does not throw an exception if the call stack is depleted but rather returns false in that case. The low-level functions .call(), .delegatecall() and .staticcall() behave in the same way.

Authorized Proxies
If your contract can act as a proxy, i.e. if it can call arbitrary contracts with user-supplied data, then the user can essentially assume the identity of the proxy contract. Even if you have other protective measures in place, it is best to build your contract system such that the proxy does not have any permissions (not even for itself). If needed, you can accomplish that using a second proxy:

open in Remix

// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.0;
contract ProxyWithMoreFunctionality {
    PermissionlessProxy proxy;

    function callOther(address addr, bytes memory payload) public
            returns (bool, bytes memory) {
        return proxy.callOther(addr, payload);
    }
    // Other functions and other functionality
}

// This is the full contract, it has no other functionality and
// requires no privileges to work.
contract PermissionlessProxy {
    function callOther(address addr, bytes memory payload) public
            returns (bool, bytes memory) {
        return addr.call(payload);
    }
}
tx.origin
Never use tx.origin for authorization. Let’s say you have a wallet contract like this:

open in Remix

// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.7.0 <0.9.0;
// THIS CONTRACT CONTAINS A BUG - DO NOT USE
contract TxUserWallet {
    address owner;

    constructor() {
        owner = msg.sender;
    }

    function transferTo(address payable dest, uint amount) public {
        // THE BUG IS RIGHT HERE, you must use msg.sender instead of tx.origin
        require(tx.origin == owner);
        dest.transfer(amount);
    }
}
Now someone tricks you into sending Ether to the address of this attack wallet:

open in Remix

// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.7.0 <0.9.0;
interface TxUserWallet {
    function transferTo(address payable dest, uint amount) external;
}

contract TxAttackWallet {
    address payable owner;

    constructor() {
        owner = payable(msg.sender);
    }

    receive() external payable {
        TxUserWallet(msg.sender).transferTo(owner, msg.sender.balance);
    }
}
If your wallet had checked msg.sender for authorization, it would get the address of the attack wallet, instead of the owner’s address. But by checking tx.origin, it gets the original address that kicked off the transaction, which is still the owner’s address. The attack wallet instantly drains all your funds.

Two’s Complement / Underflows / Overflows
As in many programming languages, Solidity’s integer types are not actually integers. They resemble integers when the values are small, but cannot represent arbitrarily large numbers.

The following code causes an overflow because the result of the addition is too large to be stored in the type uint8:

open in Remix

uint8 x = 255;
uint8 y = 1;
return x + y;
Solidity has two modes in which it deals with these overflows: Checked and Unchecked or “wrapping” mode.

The default checked mode will detect overflows and cause a failing assertion. You can disable this check using unchecked { ... }, causing the overflow to be silently ignored. The above code would return 0 if wrapped in unchecked { ... }.

Even in checked mode, do not assume you are protected from overflow bugs. In this mode, overflows will always revert. If it is not possible to avoid the overflow, this can lead to a smart contract being stuck in a certain state.

In general, read about the limits of two’s complement representation, which even has some more special edge cases for signed numbers.

Try to use require to limit the size of inputs to a reasonable range and use the SMT checker to find potential overflows.

Clearing Mappings
The Solidity type mapping (see Mapping Types) is a storage-only key-value data structure that does not keep track of the keys that were assigned a non-zero value. Because of that, cleaning a mapping without extra information about the written keys is not possible. If a mapping is used as the base type of a dynamic storage array, deleting or popping the array will have no effect over the mapping elements. The same happens, for example, if a mapping is used as the type of a member field of a struct that is the base type of a dynamic storage array. The mapping is also ignored in assignments of structs or arrays containing a mapping.

open in Remix

// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.6.0 <0.9.0;

contract Map {
    mapping(uint => uint)[] array;

    function allocate(uint newMaps) public {
        for (uint i = 0; i < newMaps; i++)
            array.push();
    }

    function writeMap(uint map, uint key, uint value) public {
        array[map][key] = value;
    }

    function readMap(uint map, uint key) public view returns (uint) {
        return array[map][key];
    }

    function eraseMaps() public {
        delete array;
    }
}
Consider the example above and the following sequence of calls: allocate(10), writeMap(4, 128, 256). At this point, calling readMap(4, 128) returns 256. If we call eraseMaps, the length of the state variable array is zeroed, but since its mapping elements cannot be zeroed, their information stays alive in the contract’s storage. After deleting array, calling allocate(5) allows us to access array[4] again, and calling readMap(4, 128) returns 256 even without another call to writeMap.

If your mapping information must be deleted, consider using a library similar to iterable mapping, allowing you to traverse the keys and delete their values in the appropriate mapping.

Internal Function Pointers in Upgradeable Contracts
Updating the code of your contract may invalidate the values of variables of internal function types. Consider such values ephemeral and avoid storing them in state variables. If you do, you must ensure that they never persist across code updates and are never used by other contracts having access to the same storage space as a result of a delegatecall or account abstraction.

Minor Details
Types that do not occupy the full 32 bytes might contain “dirty higher order bits”. This is especially important if you access msg.data - it poses a malleability risk: You can craft transactions that call a function f(uint8 x) with a raw byte argument of 0xff000001 and with 0x00000001. Both are fed to the contract and both will look like the number 1 as far as x is concerned, but msg.data will be different, so if you use keccak256(msg.data) for anything, you will get different results.

Recommendations
Take Warnings Seriously
If the compiler warns you about something, you should change it. Even if you do not think that this particular warning has security implications, there might be another issue buried beneath it. Any compiler warning we issue can be silenced by slight changes to the code.

Always use the latest version of the compiler to be notified about all recently introduced warnings.

Messages of type info, issued by the compiler, are not dangerous and simply represent extra suggestions and optional information that the compiler thinks might be useful to the user.

Restrict the Amount of Ether
Restrict the amount of Ether (or other tokens) that can be stored in a smart contract. If your source code, the compiler or the platform has a bug, these funds may be lost. If you want to limit your loss, limit the amount of Ether.

Keep it Small and Modular
Keep your contracts small and easily understandable. Single out unrelated functionality in other contracts or into libraries. General recommendations about the source code quality of course apply: Limit the amount of local variables, the length of functions and so on. Document your functions so that others can see what your intention was and whether it is different than what the code does.

Use the Checks-Effects-Interactions Pattern
Most functions will first perform some checks and they should be done first (who called the function, are the arguments in range, did they send enough Ether, does the person have tokens, etc.).

As the second step, if all checks passed, effects to the state variables of the current contract should be made. Interaction with other contracts should be the very last step in any function.

Early contracts delayed some effects and waited for external function calls to return in a non-error state. This is often a serious mistake because of the reentrancy problem explained above.

Note that, also, calls to known contracts might in turn cause calls to unknown contracts, so it is probably better to just always apply this pattern.

Include a Fail-Safe Mode
While making your system fully decentralized will remove any intermediary, it might be a good idea, especially for new code, to include some kind of fail-safe mechanism:

You can add a function in your smart contract that performs some self-checks like “Has any Ether leaked?”, “Is the sum of the tokens equal to the balance of the contract?” or similar things. Keep in mind that you cannot use too much gas for that, so help through off-chain computations might be needed there.

If the self-check fails, the contract automatically switches into some kind of “failsafe” mode, which, for example, disables most of the features, hands over control to a fixed and trusted third party or just converts the contract into a simple “give me back my Ether” contract.


List of Known Bugs
Below, you can find a JSON-formatted list of some of the known security-relevant bugs in the Solidity compiler. The file itself is hosted in the GitHub repository. The list stretches back as far as version 0.3.0, bugs known to be present only in versions preceding that are not listed.

There is another file called bugs_by_version.json, which can be used to check which bugs affect a specific version of the compiler.

Contract source verification tools and also other tools interacting with contracts should consult this list according to the following criteria:

It is mildly suspicious if a contract was compiled with a nightly compiler version instead of a released version. This list does not keep track of unreleased or nightly versions.

It is also mildly suspicious if a contract was compiled with a version that was not the most recent at the time the contract was created. For contracts created from other contracts, you have to follow the creation chain back to a transaction and use the date of that transaction as creation date.

It is highly suspicious if a contract was compiled with a compiler that contains a known bug and the contract was created at a time where a newer compiler version containing a fix was already released.

The JSON file of known bugs below is an array of objects, one for each bug, with the following keys:

uid
Unique identifier given to the bug in the form of SOL-<year>-<number>. It is possible that multiple entries exists with the same uid. This means multiple version ranges are affected by the same bug.

name
Unique name given to the bug

summary
Short description of the bug

description
Detailed description of the bug

link
URL of a website with more detailed information, optional

introduced
The first published compiler version that contained the bug, optional

fixed
The first published compiler version that did not contain the bug anymore

publish
The date at which the bug became known publicly, optional

severity
Severity of the bug: very low, low, medium, high. Takes into account discoverability in contract tests, likelihood of occurrence and potential damage by exploits.

conditions
Conditions that have to be met to trigger the bug. The following keys can be used: optimizer, Boolean value which means that the optimizer has to be switched on to enable the bug. evmVersion, a string that indicates which EVM version compiler settings trigger the bug. The string can contain comparison operators. For example, ">=constantinople" means that the bug is present when the EVM version is set to constantinople or later. If no conditions are given, assume that the bug is present.

check
This field contains different checks that report whether the smart contract contains the bug or not. The first type of check are JavaScript regular expressions that are to be matched against the source code (“source-regex”) if the bug is present. If there is no match, then the bug is very likely not present. If there is a match, the bug might be present. For improved accuracy, the checks should be applied to the source code after stripping comments. The second type of check are patterns to be checked on the compact AST of the Solidity program (“ast-compact-json-path”). The specified search query is a JsonPath expression. If at least one path of the Solidity AST matches the query, the bug is likely present.

[
    {
        "uid": "SOL-2023-3",
        "name": "VerbatimInvalidDeduplication",
        "summary": "All ``verbatim`` blocks are considered identical by deduplicator and can incorrectly be unified when surrounded by identical opcodes.",
        "description": "The block deduplicator is a step of the opcode-based optimizer which identifies equivalent assembly blocks and merges them into a single one. However, when blocks contained ``verbatim``, their comparison was performed incorrectly, leading to the collapse of assembly blocks which are identical except for the contents of the ``verbatim`` items. Since ``verbatim`` is only available in Yul, compilation of Solidity sources is not affected.",
        "link": "https://blog.soliditylang.org/2023/11/08/verbatim-invalid-deduplication-bug/",
        "introduced": "0.8.5",
        "fixed": "0.8.23",
        "severity": "low"
    },
    {
        "uid": "SOL-2023-2",
        "name": "FullInlinerNonExpressionSplitArgumentEvaluationOrder",
        "summary": "Optimizer sequences containing FullInliner do not preserve the evaluation order of arguments of inlined function calls in code that is not in expression-split form.",
        "description": "Function call arguments in Yul are evaluated right to left. This order matters when the argument expressions have side-effects, and changing it may change contract behavior. FullInliner is an optimizer step that can replace a function call with the body of that function. The transformation involves assigning argument expressions to temporary variables, which imposes an explicit evaluation order. FullInliner was written with the assumption that this order does not necessarily have to match usual argument evaluation order because the argument expressions have no side-effects. In most circumstances this assumption is true because the default optimization step sequence contains the ExpressionSplitter step. ExpressionSplitter ensures that the code is in *expression-split form*, which means that function calls cannot appear nested inside expressions, and all function call arguments have to be variables. The assumption is, however, not guaranteed to be true in general. Version 0.6.7 introduced a setting allowing users to specify an arbitrary optimization step sequence, making it possible for the FullInliner to actually encounter argument expressions with side-effects, which can result in behavior differences between optimized and unoptimized bytecode. Contracts compiled without optimization or with the default optimization sequence are not affected. To trigger the bug the user has to explicitly choose compiler settings that contain a sequence with FullInliner step not preceded by ExpressionSplitter.",
        "link": "https://blog.soliditylang.org/2023/07/19/full-inliner-non-expression-split-argument-evaluation-order-bug/",
        "introduced": "0.6.7",
        "fixed": "0.8.21",
        "severity": "low",
        "conditions": {
            "yulOptimizer": true
        }
    },
    {
        "uid": "SOL-2023-1",
        "name": "MissingSideEffectsOnSelectorAccess",
        "summary": "Accessing the ``.selector`` member on complex expressions leaves the expression unevaluated in the legacy code generation.",
        "description": "When accessing the ``.selector`` member on an expression with side-effects, like an assignment, a function call or a conditional, the expression would not be evaluated in the legacy code generation. This would happen in expressions where the functions used in the expression were all known at compilation time, regardless of whether the whole expression could be evaluated at compilation time or not. Note that the code generated by the IR pipeline was unaffected and would behave as expected.",
        "link": "https://blog.soliditylang.org/2023/07/19/missing-side-effects-on-selector-access-bug/",
        "introduced": "0.6.2",
        "fixed": "0.8.21",
        "severity": "low",
        "conditions": {
            "viaIR": false
        }
    },
    {
        "uid": "SOL-2022-7",
        "name": "StorageWriteRemovalBeforeConditionalTermination",
        "summary": "Calling functions that conditionally terminate the external EVM call using the assembly statements ``return(...)`` or ``stop()`` may result in incorrect removals of prior storage writes.",
        "description": "A call to a Yul function that conditionally terminates the external EVM call could result in prior storage writes being incorrectly removed by the Yul optimizer. This used to happen in cases in which it would have been valid to remove the store, if the Yul function in question never actually terminated the external call, and the control flow always returned back to the caller instead. Conditional termination within the same Yul block instead of within a called function was not affected. In Solidity with optimized via-IR code generation, any storage write before a function conditionally calling ``return(...)`` or ``stop()`` in inline assembly, may have been incorrectly removed, whenever it would have been valid to remove the write without the ``return(...)`` or ``stop()``. In optimized legacy code generation, only inline assembly that did not refer to any Solidity variables and that involved conditionally-terminating user-defined assembly functions could be affected.",
        "link": "https://blog.soliditylang.org/2022/09/08/storage-write-removal-before-conditional-termination/",
        "introduced": "0.8.13",
        "fixed": "0.8.17",
        "severity": "medium/high",
        "conditions": {
            "yulOptimizer": true
        }
    },
    {
        "uid": "SOL-2022-6",
        "name": "AbiReencodingHeadOverflowWithStaticArrayCleanup",
        "summary": "ABI-encoding a tuple with a statically-sized calldata array in the last component would corrupt 32 leading bytes of its first dynamically encoded component.",
        "description": "When ABI-encoding a statically-sized calldata array, the compiler always pads the data area to a multiple of 32-bytes and ensures that the padding bytes are zeroed. In some cases, this cleanup used to be performed by always writing exactly 32 bytes, regardless of how many needed to be zeroed. This was done with the assumption that the data that would eventually occupy the area past the end of the array had not yet been written, because the encoder processes tuple components in the order they were given. While this assumption is mostly true, there is an important corner case: dynamically encoded tuple components are stored separately from the statically-sized ones in an area called the *tail* of the encoding and the tail immediately follows the *head*, which is where the statically-sized components are placed. The aforementioned cleanup, if performed for the last component of the head would cross into the tail and overwrite up to 32 bytes of the first component stored there with zeros. The only array type for which the cleanup could actually result in an overwrite were arrays with ``uint256`` or ``bytes32`` as the base element type and in this case the size of the corrupted area was always exactly 32 bytes. The problem affected tuples at any nesting level. This included also structs, which are encoded as tuples in the ABI. Note also that lists of parameters and return values of functions, events and errors are encoded as tuples.",
        "link": "https://blog.soliditylang.org/2022/08/08/calldata-tuple-reencoding-head-overflow-bug/",
        "introduced": "0.5.8",
        "fixed": "0.8.16",
        "severity": "medium",
        "conditions": {
            "ABIEncoderV2": true
        }
    },
    {
        "uid": "SOL-2022-5",
        "name": "DirtyBytesArrayToStorage",
        "summary": "Copying ``bytes`` arrays from memory or calldata to storage may result in dirty storage values.",
        "description": "Copying ``bytes`` arrays from memory or calldata to storage is done in chunks of 32 bytes even if the length is not a multiple of 32. Thereby, extra bytes past the end of the array may be copied from calldata or memory to storage. These dirty bytes may then become observable after a ``.push()`` without arguments to the bytes array in storage, i.e. such a push will not result in a zero value at the end of the array as expected. This bug only affects the legacy code generation pipeline, the new code generation pipeline via IR is not affected.",
        "link": "https://blog.soliditylang.org/2022/06/15/dirty-bytes-array-to-storage-bug/",
        "introduced": "0.0.1",
        "fixed": "0.8.15",
        "severity": "low"
    },
    {
        "uid": "SOL-2022-4",
        "name": "InlineAssemblyMemorySideEffects",
        "summary": "The Yul optimizer may incorrectly remove memory writes from inline assembly blocks, that do not access solidity variables.",
        "description": "The Yul optimizer considers all memory writes in the outermost Yul block that are never read from as unused and removes them. This is valid when that Yul block is the entire Yul program, which is always the case for the Yul code generated by the new via-IR pipeline. Inline assembly blocks are never optimized in isolation when using that pipeline. Instead they are optimized as a part of the whole Yul input. However, the legacy code generation pipeline (which is still the default) runs the Yul optimizer individually on an inline assembly block if the block does not refer to any local variables defined in the surrounding Solidity code. Consequently, memory writes in such inline assembly blocks are removed as well, if the written memory is never read from in the same assembly block, even if the written memory is accessed later, for example by a subsequent inline assembly block.",
        "link": "https://blog.soliditylang.org/2022/06/15/inline-assembly-memory-side-effects-bug/",
        "introduced": "0.8.13",
        "fixed": "0.8.15",
        "severity": "medium",
        "conditions": {
            "yulOptimizer": true
        }
    },
    {
        "uid": "SOL-2022-3",
        "name": "DataLocationChangeInInternalOverride",
        "summary": "It was possible to change the data location of the parameters or return variables from ``calldata`` to ``memory`` and vice-versa while overriding internal and public functions. This caused invalid code to be generated when calling such a function internally through virtual function calls.",
        "description": "When calling external functions, it is irrelevant if the data location of the parameters is ``calldata`` or ``memory``, the encoding of the data does not change. Because of that, changing the data location when overriding external functions is allowed. The compiler incorrectly also allowed a change in the data location for overriding public and internal functions. Since public functions can be called internally as well as externally, this causes invalid code to be generated when such an incorrectly overridden function is called internally through the base contract. The caller provides a memory pointer, but the called function interprets it as a calldata pointer or vice-versa.",
        "link": "https://blog.soliditylang.org/2022/05/17/data-location-inheritance-bug/",
        "introduced": "0.6.9",
        "fixed": "0.8.14",
        "severity": "very low"
    },
    {
        "uid": "SOL-2022-2",
        "name": "NestedCalldataArrayAbiReencodingSizeValidation",
        "summary": "ABI-reencoding of nested dynamic calldata arrays did not always perform proper size checks against the size of calldata and could read beyond ``calldatasize()``.",
        "description": "Calldata validation for nested dynamic types is deferred until the first access to the nested values. Such an access may for example be a copy to memory or an index or member access to the outer type. While in most such accesses calldata validation correctly checks that the data area of the nested array is completely contained in the passed calldata (i.e. in the range [0, calldatasize()]), this check may not be performed, when ABI encoding such nested types again directly from calldata. For instance, this can happen, if a value in calldata with a nested dynamic array is passed to an external call, used in ``abi.encode`` or emitted as event. In such cases, if the data area of the nested array extends beyond ``calldatasize()``, ABI encoding it did not revert, but continued reading values from beyond ``calldatasize()`` (i.e. zero values).",
        "link": "https://blog.soliditylang.org/2022/05/17/calldata-reencode-size-check-bug/",
        "introduced": "0.5.8",
        "fixed": "0.8.14",
        "severity": "very low"
    },
    {
        "uid": "SOL-2022-1",
        "name": "AbiEncodeCallLiteralAsFixedBytesBug",
        "summary": "Literals used for a fixed length bytes parameter in ``abi.encodeCall`` were encoded incorrectly.",
        "description": "For the encoding, the compiler only considered the types of the expressions in the second argument of ``abi.encodeCall`` itself, but not the parameter types of the function given as first argument. In almost all cases the abi encoding of the type of the expression matches the abi encoding of the parameter type of the given function. This is because the type checker ensures the expression is implicitly convertible to the respective parameter type. However this is not true for number literals used for fixed bytes types shorter than 32 bytes, nor for string literals used for any fixed bytes type. Number literals were encoded as numbers instead of being shifted to become left-aligned. String literals were encoded as dynamically sized memory strings instead of being converted to a left-aligned bytes value.",
        "link": "https://blog.soliditylang.org/2022/03/16/encodecall-bug/",
        "introduced": "0.8.11",
        "fixed": "0.8.13",
        "severity": "very low"

    },
    {
        "uid": "SOL-2021-4",
        "name": "UserDefinedValueTypesBug",
        "summary": "User defined value types with underlying type shorter than 32 bytes used incorrect storage layout and wasted storage",
        "description": "The compiler did not correctly compute the storage layout of user defined value types based on types that are shorter than 32 bytes. It would always use a full storage slot for these types, even if the underlying type was shorter. This was wasteful and might have problems with tooling or contract upgrades.",
        "link": "https://blog.soliditylang.org/2021/09/29/user-defined-value-types-bug/",
        "introduced": "0.8.8",
        "fixed": "0.8.9",
        "severity": "very low"
    },
    {
        "uid": "SOL-2021-3",
        "name": "SignedImmutables",
        "summary": "Immutable variables of signed integer type shorter than 256 bits can lead to values with invalid higher order bits if inline assembly is used.",
        "description": "When immutable variables of signed integer type shorter than 256 bits are read, their higher order bits were unconditionally set to zero. The correct operation would be to sign-extend the value, i.e. set the higher order bits to one if the sign bit is one. This sign-extension is performed by Solidity just prior to when it matters, i.e. when a value is stored in memory, when it is compared or when a division is performed. Because of that, to our knowledge, the only way to access the value in its unclean state is by reading it through inline assembly.",
        "link": "https://blog.soliditylang.org/2021/09/29/signed-immutables-bug/",
        "introduced": "0.6.5",
        "fixed": "0.8.9",
        "severity": "very low"
    },
    {
        "uid": "SOL-2021-2",
        "name": "ABIDecodeTwoDimensionalArrayMemory",
        "summary": "If used on memory byte arrays, result of the function ``abi.decode`` can depend on the contents of memory outside of the actual byte array that is decoded.",
        "description": "The ABI specification uses pointers to data areas for everything that is dynamically-sized. When decoding data from memory (instead of calldata), the ABI decoder did not properly validate some of these pointers. More specifically, it was possible to use large values for the pointers inside arrays such that computing the offset resulted in an undetected overflow. This could lead to these pointers targeting areas in memory outside of the actual area to be decoded. This way, it was possible for ``abi.decode`` to return different values for the same encoded byte array.",
        "link": "https://blog.soliditylang.org/2021/04/21/decoding-from-memory-bug/",
        "introduced": "0.4.16",
        "fixed": "0.8.4",
        "conditions": {
            "ABIEncoderV2": true
        },
        "severity": "very low"
    },
    {
        "uid": "SOL-2021-1",
        "name": "KeccakCaching",
        "summary": "The bytecode optimizer incorrectly reused previously evaluated Keccak-256 hashes. You are unlikely to be affected if you do not compute Keccak-256 hashes in inline assembly.",
        "description": "Solidity's bytecode optimizer has a step that can compute Keccak-256 hashes, if the contents of the memory are known during compilation time. This step also has a mechanism to determine that two Keccak-256 hashes are equal even if the values in memory are not known during compile time. This mechanism had a bug where Keccak-256 of the same memory content, but different sizes were considered equal. More specifically, ``keccak256(mpos1, length1)`` and ``keccak256(mpos2, length2)`` in some cases were considered equal if ``length1`` and ``length2``, when rounded up to nearest multiple of 32 were the same, and when the memory contents at ``mpos1`` and ``mpos2`` can be deduced to be equal. You maybe affected if you compute multiple Keccak-256 hashes of the same content, but with different lengths inside inline assembly. You are unaffected if your code uses ``keccak256`` with a length that is not a compile-time constant or if it is always a multiple of 32.",
        "link": "https://blog.soliditylang.org/2021/03/23/keccak-optimizer-bug/",
        "fixed": "0.8.3",
        "conditions": {
            "optimizer": true
        },
        "severity": "medium"
    },
    {
        "uid": "SOL-2020-11",
        "name": "EmptyByteArrayCopy",
        "summary": "Copying an empty byte array (or string) from memory or calldata to storage can result in data corruption if the target array's length is increased subsequently without storing new data.",
        "description": "The routine that copies byte arrays from memory or calldata to storage stores unrelated data from after the source array in the storage slot if the source array is empty. If the storage array's length is subsequently increased either by using ``.push()`` or by assigning to its ``.length`` attribute (only before 0.6.0), the newly created byte array elements will not be zero-initialized, but contain the unrelated data. You are not affected if you do not assign to ``.length`` and do not use ``.push()`` on byte arrays, or only use ``.push(<arg>)`` or manually initialize the new elements.",
        "link": "https://blog.soliditylang.org/2020/10/19/empty-byte-array-copy-bug/",
        "fixed": "0.7.4",
        "severity": "medium"
    },
    {
        "uid": "SOL-2020-10",
        "name": "DynamicArrayCleanup",
        "summary": "When assigning a dynamically-sized array with types of size at most 16 bytes in storage causing the assigned array to shrink, some parts of deleted slots were not zeroed out.",
        "description": "Consider a dynamically-sized array in storage whose base-type is small enough such that multiple values can be packed into a single slot, such as `uint128[]`. Let us define its length to be `l`. When this array gets assigned from another array with a smaller length, say `m`, the slots between elements `m` and `l` have to be cleaned by zeroing them out. However, this cleaning was not performed properly. Specifically, after the slot corresponding to `m`, only the first packed value was cleaned up. If this array gets resized to a length larger than `m`, the indices corresponding to the unclean parts of the slot contained the original value, instead of 0. The resizing here is performed by assigning to the array `length`, by a `push()` or via inline assembly. You are not affected if you are only using `.push(<arg>)` or if you assign a value (even zero) to the new elements after increasing the length of the array.",
        "link": "https://blog.soliditylang.org/2020/10/07/solidity-dynamic-array-cleanup-bug/",
        "fixed": "0.7.3",
        "severity": "medium"
    },
    {
        "uid": "SOL-2020-9",
        "name": "FreeFunctionRedefinition",
        "summary": "The compiler does not flag an error when two or more free functions with the same name and parameter types are defined in a source unit or when an imported free function alias shadows another free function with a different name but identical parameter types.",
        "description": "In contrast to functions defined inside contracts, free functions with identical names and parameter types did not create an error. Both definition of free functions with identical name and parameter types and an imported free function with an alias that shadows another function with a different name but identical parameter types were permitted due to which a call to either the multiply defined free function or the imported free function alias within a contract led to the execution of that free function which was defined first within the source unit. Subsequently defined identical free function definitions were silently ignored and their code generation was skipped.",
        "introduced": "0.7.1",
        "fixed": "0.7.2",
        "severity": "low"
    },
    {
        "uid": "SOL-2020-8",
        "name": "UsingForCalldata",
        "summary": "Function calls to internal library functions with calldata parameters called via ``using for`` can result in invalid data being read.",
        "description": "Function calls to internal library functions using the ``using for`` mechanism copied all calldata parameters to memory first and passed them on like that, regardless of whether it was an internal or an external call. Due to that, the called function would receive a memory pointer that is interpreted as a calldata pointer. Since dynamically sized arrays are passed using two stack slots for calldata, but only one for memory, this can lead to stack corruption. An affected library call will consider the JUMPDEST to which it is supposed to return as part of its arguments and will instead jump out to whatever was on the stack before the call.",
        "introduced": "0.6.9",
        "fixed": "0.6.10",
        "severity": "very low"
    },
    {
        "uid": "SOL-2020-7",
        "name": "MissingEscapingInFormatting",
        "summary": "String literals containing double backslash characters passed directly to external or encoding function calls can lead to a different string being used when ABIEncoderV2 is enabled.",
        "description": "When ABIEncoderV2 is enabled, string literals passed directly to encoding functions or external function calls are stored as strings in the intermediate code. Characters outside the printable range are handled correctly, but backslashes are not escaped in this procedure. This leads to double backslashes being reduced to single backslashes and consequently re-interpreted as escapes potentially resulting in a different string being encoded.",
        "introduced": "0.5.14",
        "fixed": "0.6.8",
        "severity": "very low",
        "conditions": {
            "ABIEncoderV2": true
        }
    },
    {
        "uid": "SOL-2020-6",
        "name": "ArraySliceDynamicallyEncodedBaseType",
        "summary": "Accessing array slices of arrays with dynamically encoded base types (e.g. multi-dimensional arrays) can result in invalid data being read.",
        "description": "For arrays with dynamically sized base types, index range accesses that use a start expression that is non-zero will result in invalid array slices. Any index access to such array slices will result in data being read from incorrect calldata offsets. Array slices are only supported for dynamic calldata types and all problematic type require ABIEncoderV2 to be enabled.",
        "introduced": "0.6.0",
        "fixed": "0.6.8",
        "severity": "very low",
        "conditions": {
            "ABIEncoderV2": true
        }
    },
    {
        "uid": "SOL-2020-5",
        "name": "ImplicitConstructorCallvalueCheck",
        "summary": "The creation code of a contract that does not define a constructor but has a base that does define a constructor did not revert for calls with non-zero value.",
        "description": "Starting from Solidity 0.4.5 the creation code of contracts without explicit payable constructor is supposed to contain a callvalue check that results in contract creation reverting, if non-zero value is passed. However, this check was missing in case no explicit constructor was defined in a contract at all, but the contract has a base that does define a constructor. In these cases it is possible to send value in a contract creation transaction or using inline assembly without revert, even though the creation code is supposed to be non-payable.",
        "introduced": "0.4.5",
        "fixed": "0.6.8",
        "severity": "very low"
    },
    {
        "uid": "SOL-2020-4",
        "name": "TupleAssignmentMultiStackSlotComponents",
        "summary": "Tuple assignments with components that occupy several stack slots, i.e. nested tuples, pointers to external functions or references to dynamically sized calldata arrays, can result in invalid values.",
        "description": "Tuple assignments did not correctly account for tuple components that occupy multiple stack slots in case the number of stack slots differs between left-hand-side and right-hand-side. This can either happen in the presence of nested tuples or if the right-hand-side contains external function pointers or references to dynamic calldata arrays, while the left-hand-side contains an omission.",
        "introduced": "0.1.6",
        "fixed": "0.6.6",
        "severity": "very low"
    },
    {
        "uid": "SOL-2020-3",
        "name": "MemoryArrayCreationOverflow",
        "summary": "The creation of very large memory arrays can result in overlapping memory regions and thus memory corruption.",
        "description": "No runtime overflow checks were performed for the length of memory arrays during creation. In cases for which the memory size of an array in bytes, i.e. the array length times 32, is larger than 2^256-1, the memory allocation will overflow, potentially resulting in overlapping memory areas. The length of the array is still stored correctly, so copying or iterating over such an array will result in out-of-gas.",
        "link": "https://blog.soliditylang.org/2020/04/06/memory-creation-overflow-bug/",
        "introduced": "0.2.0",
        "fixed": "0.6.5",
        "severity": "low"
    },
    {
        "uid": "SOL-2020-1",
        "name": "YulOptimizerRedundantAssignmentBreakContinue",
        "summary": "The Yul optimizer can remove essential assignments to variables declared inside for loops when Yul's continue or break statement is used. You are unlikely to be affected if you do not use inline assembly with for loops and continue and break statements.",
        "description": "The Yul optimizer has a stage that removes assignments to variables that are overwritten again or are not used in all following control-flow branches. This logic incorrectly removes such assignments to variables declared inside a for loop if they can be removed in a control-flow branch that ends with ``break`` or ``continue`` even though they cannot be removed in other control-flow branches. Variables declared outside of the respective for loop are not affected.",
        "introduced": "0.6.0",
        "fixed": "0.6.1",
        "severity": "medium",
        "conditions": {
            "yulOptimizer": true
        }
    },
    {
        "uid": "SOL-2020-2",
        "name": "privateCanBeOverridden",
        "summary": "Private methods can be overridden by inheriting contracts.",
        "description": "While private methods of base contracts are not visible and cannot be called directly from the derived contract, it is still possible to declare a function of the same name and type and thus change the behaviour of the base contract's function.",
        "introduced": "0.3.0",
        "fixed": "0.5.17",
        "severity": "low"
    },
    {
        "uid": "SOL-2020-1",
        "name": "YulOptimizerRedundantAssignmentBreakContinue0.5",
        "summary": "The Yul optimizer can remove essential assignments to variables declared inside for loops when Yul's continue or break statement is used. You are unlikely to be affected if you do not use inline assembly with for loops and continue and break statements.",
        "description": "The Yul optimizer has a stage that removes assignments to variables that are overwritten again or are not used in all following control-flow branches. This logic incorrectly removes such assignments to variables declared inside a for loop if they can be removed in a control-flow branch that ends with ``break`` or ``continue`` even though they cannot be removed in other control-flow branches. Variables declared outside of the respective for loop are not affected.",
        "introduced": "0.5.8",
        "fixed": "0.5.16",
        "severity": "low",
        "conditions": {
            "yulOptimizer": true
        }
    },
    {
        "uid": "SOL-2019-10",
        "name": "ABIEncoderV2LoopYulOptimizer",
        "summary": "If both the experimental ABIEncoderV2 and the experimental Yul optimizer are activated, one component of the Yul optimizer may reuse data in memory that has been changed in the meantime.",
        "description": "The Yul optimizer incorrectly replaces ``mload`` and ``sload`` calls with values that have been previously written to the load location (and potentially changed in the meantime) if all of the following conditions are met: (1) there is a matching ``mstore`` or ``sstore`` call before; (2) the contents of memory or storage is only changed in a function that is called (directly or indirectly) in between the first store and the load call; (3) called function contains a for loop where the same memory location is changed in the condition or the post or body block. When used in Solidity mode, this can only happen if the experimental ABIEncoderV2 is activated and the experimental Yul optimizer has been activated manually in addition to the regular optimizer in the compiler settings.",
        "introduced": "0.5.14",
        "fixed": "0.5.15",
        "severity": "low",
        "conditions": {
            "ABIEncoderV2": true,
            "optimizer": true,
            "yulOptimizer": true
        }
    },
    {
        "uid": "SOL-2019-9",
        "name": "ABIEncoderV2CalldataStructsWithStaticallySizedAndDynamicallyEncodedMembers",
        "summary": "Reading from calldata structs that contain dynamically encoded, but statically-sized members can result in incorrect values.",
        "description": "When a calldata struct contains a dynamically encoded, but statically-sized member, the offsets for all subsequent struct members are calculated incorrectly. All reads from such members will result in invalid values. Only calldata structs are affected, i.e. this occurs in external functions with such structs as argument. Using affected structs in storage or memory or as arguments to public functions on the other hand works correctly.",
        "introduced": "0.5.6",
        "fixed": "0.5.11",
        "severity": "low",
        "conditions": {
            "ABIEncoderV2": true
        }
    },
    {
        "uid": "SOL-2019-8",
        "name": "SignedArrayStorageCopy",
        "summary": "Assigning an array of signed integers to a storage array of different type can lead to data corruption in that array.",
        "description": "In two's complement, negative integers have their higher order bits set. In order to fit into a shared storage slot, these have to be set to zero. When a conversion is done at the same time, the bits to set to zero were incorrectly determined from the source and not the target type. This means that such copy operations can lead to incorrect values being stored.",
        "link": "https://blog.soliditylang.org/2019/06/25/solidity-storage-array-bugs/",
        "introduced": "0.4.7",
        "fixed": "0.5.10",
        "severity": "low/medium"
    },
    {
        "uid": "SOL-2019-7",
        "name": "ABIEncoderV2StorageArrayWithMultiSlotElement",
        "summary": "Storage arrays containing structs or other statically-sized arrays are not read properly when directly encoded in external function calls or in abi.encode*.",
        "description": "When storage arrays whose elements occupy more than a single storage slot are directly encoded in external function calls or using abi.encode*, their elements are read in an overlapping manner, i.e. the element pointer is not properly advanced between reads. This is not a problem when the storage data is first copied to a memory variable or if the storage array only contains value types or dynamically-sized arrays.",
        "link": "https://blog.soliditylang.org/2019/06/25/solidity-storage-array-bugs/",
        "introduced": "0.4.16",
        "fixed": "0.5.10",
        "severity": "low",
        "conditions": {
            "ABIEncoderV2": true
        }
    },
    {
        "uid": "SOL-2019-6",
        "name": "DynamicConstructorArgumentsClippedABIV2",
        "summary": "A contract's constructor that takes structs or arrays that contain dynamically-sized arrays reverts or decodes to invalid data.",
        "description": "During construction of a contract, constructor parameters are copied from the code section to memory for decoding. The amount of bytes to copy was calculated incorrectly in case all parameters are statically-sized but contain dynamically-sized arrays as struct members or inner arrays. Such types are only available if ABIEncoderV2 is activated.",
        "introduced": "0.4.16",
        "fixed": "0.5.9",
        "severity": "very low",
        "conditions": {
            "ABIEncoderV2": true
        }
    },
    {
        "uid": "SOL-2019-5",
        "name": "UninitializedFunctionPointerInConstructor",
        "summary": "Calling uninitialized internal function pointers created in the constructor does not always revert and can cause unexpected behaviour.",
        "description": "Uninitialized internal function pointers point to a special piece of code that causes a revert when called. Jump target positions are different during construction and after deployment, but the code for setting this special jump target only considered the situation after deployment.",
        "introduced": "0.5.0",
        "fixed": "0.5.8",
        "severity": "very low"
    },
    {
        "uid": "SOL-2019-5",
        "name": "UninitializedFunctionPointerInConstructor_0.4.x",
        "summary": "Calling uninitialized internal function pointers created in the constructor does not always revert and can cause unexpected behaviour.",
        "description": "Uninitialized internal function pointers point to a special piece of code that causes a revert when called. Jump target positions are different during construction and after deployment, but the code for setting this special jump target only considered the situation after deployment.",
        "introduced": "0.4.5",
        "fixed": "0.4.26",
        "severity": "very low"
    },
    {
        "uid": "SOL-2019-4",
        "name": "IncorrectEventSignatureInLibraries",
        "summary": "Contract types used in events in libraries cause an incorrect event signature hash",
        "description": "Instead of using the type `address` in the hashed signature, the actual contract name was used, leading to a wrong hash in the logs.",
        "introduced": "0.5.0",
        "fixed": "0.5.8",
        "severity": "very low"
    },
    {
        "uid": "SOL-2019-4",
        "name": "IncorrectEventSignatureInLibraries_0.4.x",
        "summary": "Contract types used in events in libraries cause an incorrect event signature hash",
        "description": "Instead of using the type `address` in the hashed signature, the actual contract name was used, leading to a wrong hash in the logs.",
        "introduced": "0.3.0",
        "fixed": "0.4.26",
        "severity": "very low"
    },
    {
        "uid": "SOL-2019-3",
        "name": "ABIEncoderV2PackedStorage",
        "summary": "Storage structs and arrays with types shorter than 32 bytes can cause data corruption if encoded directly from storage using the experimental ABIEncoderV2.",
        "description": "Elements of structs and arrays that are shorter than 32 bytes are not properly decoded from storage when encoded directly (i.e. not via a memory type) using ABIEncoderV2. This can cause corruption in the values themselves but can also overwrite other parts of the encoded data.",
        "link": "https://blog.soliditylang.org/2019/03/26/solidity-optimizer-and-abiencoderv2-bug/",
        "introduced": "0.5.0",
        "fixed": "0.5.7",
        "severity": "low",
        "conditions": {
            "ABIEncoderV2": true
        }
    },
    {
        "uid": "SOL-2019-3",
        "name": "ABIEncoderV2PackedStorage_0.4.x",
        "summary": "Storage structs and arrays with types shorter than 32 bytes can cause data corruption if encoded directly from storage using the experimental ABIEncoderV2.",
        "description": "Elements of structs and arrays that are shorter than 32 bytes are not properly decoded from storage when encoded directly (i.e. not via a memory type) using ABIEncoderV2. This can cause corruption in the values themselves but can also overwrite other parts of the encoded data.",
        "link": "https://blog.soliditylang.org/2019/03/26/solidity-optimizer-and-abiencoderv2-bug/",
        "introduced": "0.4.19",
        "fixed": "0.4.26",
        "severity": "low",
        "conditions": {
            "ABIEncoderV2": true
        }
    },
    {
        "uid": "SOL-2019-2",
        "name": "IncorrectByteInstructionOptimization",
        "summary": "The optimizer incorrectly handles byte opcodes whose second argument is 31 or a constant expression that evaluates to 31. This can result in unexpected values.",
        "description": "The optimizer incorrectly handles byte opcodes that use the constant 31 as second argument. This can happen when performing index access on bytesNN types with a compile-time constant value (not index) of 31 or when using the byte opcode in inline assembly.",
        "link": "https://blog.soliditylang.org/2019/03/26/solidity-optimizer-and-abiencoderv2-bug/",
        "introduced": "0.5.5",
        "fixed": "0.5.7",
        "severity": "very low",
        "conditions": {
            "optimizer": true
        }
    },
    {
        "uid": "SOL-2019-1",
        "name": "DoubleShiftSizeOverflow",
        "summary": "Double bitwise shifts by large constants whose sum overflows 256 bits can result in unexpected values.",
        "description": "Nested logical shift operations whose total shift size is 2**256 or more are incorrectly optimized. This only applies to shifts by numbers of bits that are compile-time constant expressions.",
        "link": "https://blog.soliditylang.org/2019/03/26/solidity-optimizer-and-abiencoderv2-bug/",
        "introduced": "0.5.5",
        "fixed": "0.5.6",
        "severity": "low",
        "conditions": {
            "optimizer": true,
            "evmVersion": ">=constantinople"
        }
    },
    {
        "uid": "SOL-2018-4",
        "name": "ExpExponentCleanup",
        "summary": "Using the ** operator with an exponent of type shorter than 256 bits can result in unexpected values.",
        "description": "Higher order bits in the exponent are not properly cleaned before the EXP opcode is applied if the type of the exponent expression is smaller than 256 bits and not smaller than the type of the base. In that case, the result might be larger than expected if the exponent is assumed to lie within the value range of the type. Literal numbers as exponents are unaffected as are exponents or bases of type uint256.",
        "link": "https://blog.soliditylang.org/2018/09/13/solidity-bugfix-release/",
        "fixed": "0.4.25",
        "severity": "medium/high",
        "check": {"regex-source": "[^/]\\*\\* *[^/0-9 ]"}
    },
    {
        "uid": "SOL-2018-3",
        "name": "EventStructWrongData",
        "summary": "Using structs in events logged wrong data.",
        "description": "If a struct is used in an event, the address of the struct is logged instead of the actual data.",
        "link": "https://blog.soliditylang.org/2018/09/13/solidity-bugfix-release/",
        "introduced": "0.4.17",
        "fixed": "0.4.25",
        "severity": "very low",
        "check": {"ast-compact-json-path": "$..[?(@.nodeType === 'EventDefinition')]..[?(@.nodeType === 'UserDefinedTypeName' && @.typeDescriptions.typeString.startsWith('struct'))]"}
    },
    {
        "uid": "SOL-2018-2",
        "name": "NestedArrayFunctionCallDecoder",
        "summary": "Calling functions that return multi-dimensional fixed-size arrays can result in memory corruption.",
        "description": "If Solidity code calls a function that returns a multi-dimensional fixed-size array, array elements are incorrectly interpreted as memory pointers and thus can cause memory corruption if the return values are accessed. Calling functions with multi-dimensional fixed-size arrays is unaffected as is returning fixed-size arrays from function calls. The regular expression only checks if such functions are present, not if they are called, which is required for the contract to be affected.",
        "link": "https://blog.soliditylang.org/2018/09/13/solidity-bugfix-release/",
        "introduced": "0.1.4",
        "fixed": "0.4.22",
        "severity": "medium",
        "check": {"regex-source": "returns[^;{]*\\[\\s*[^\\] \\t\\r\\n\\v\\f][^\\]]*\\]\\s*\\[\\s*[^\\] \\t\\r\\n\\v\\f][^\\]]*\\][^{;]*[;{]"}
    },
    {
        "uid": "SOL-2018-1",
        "name": "OneOfTwoConstructorsSkipped",
        "summary": "If a contract has both a new-style constructor (using the constructor keyword) and an old-style constructor (a function with the same name as the contract) at the same time, one of them will be ignored.",
        "description": "If a contract has both a new-style constructor (using the constructor keyword) and an old-style constructor (a function with the same name as the contract) at the same time, one of them will be ignored. There will be a compiler warning about the old-style constructor, so contracts only using new-style constructors are fine.",
        "introduced": "0.4.22",
        "fixed": "0.4.23",
        "severity": "very low"
    },
    {
        "uid": "SOL-2017-5",
        "name": "ZeroFunctionSelector",
        "summary": "It is possible to craft the name of a function such that it is executed instead of the fallback function in very specific circumstances.",
        "description": "If a function has a selector consisting only of zeros, is payable and part of a contract that does not have a fallback function and at most five external functions in total, this function is called instead of the fallback function if Ether is sent to the contract without data.",
        "fixed": "0.4.18",
        "severity": "very low"
    },
    {
        "uid": "SOL-2017-4",
        "name": "DelegateCallReturnValue",
        "summary": "The low-level .delegatecall() does not return the execution outcome, but converts the value returned by the functioned called to a boolean instead.",
        "description": "The return value of the low-level .delegatecall() function is taken from a position in memory, where the call data or the return data resides. This value is interpreted as a boolean and put onto the stack. This means if the called function returns at least 32 zero bytes, .delegatecall() returns false even if the call was successful.",
        "introduced": "0.3.0",
        "fixed": "0.4.15",
        "severity": "low"
    },
    {
        "uid": "SOL-2017-3",
        "name": "ECRecoverMalformedInput",
        "summary": "The ecrecover() builtin can return garbage for malformed input.",
        "description": "The ecrecover precompile does not properly signal failure for malformed input (especially in the 'v' argument) and thus the Solidity function can return data that was previously present in the return area in memory.",
        "fixed": "0.4.14",
        "severity": "medium"
    },
    {
        "uid": "SOL-2017-2",
        "name": "SkipEmptyStringLiteral",
        "summary": "If \"\" is used in a function call, the following function arguments will not be correctly passed to the function.",
        "description": "If the empty string literal \"\" is used as an argument in a function call, it is skipped by the encoder. This has the effect that the encoding of all arguments following this is shifted left by 32 bytes and thus the function call data is corrupted.",
        "fixed": "0.4.12",
        "severity": "low"
    },
    {
        "uid": "SOL-2017-1",
        "name": "ConstantOptimizerSubtraction",
        "summary": "In some situations, the optimizer replaces certain numbers in the code with routines that compute different numbers.",
        "description": "The optimizer tries to represent any number in the bytecode by routines that compute them with less gas. For some special numbers, an incorrect routine is generated. This could allow an attacker to e.g. trick victims about a specific amount of ether, or function calls to call different functions (or none at all).",
        "link": "https://blog.soliditylang.org/2017/05/03/solidity-optimizer-bug/",
        "fixed": "0.4.11",
        "severity": "low",
        "conditions": {
            "optimizer": true
        }
    },
    {
        "uid": "SOL-2016-11",
        "name": "IdentityPrecompileReturnIgnored",
        "summary": "Failure of the identity precompile was ignored.",
        "description": "Calls to the identity contract, which is used for copying memory, ignored its return value. On the public chain, calls to the identity precompile can be made in a way that they never fail, but this might be different on private chains.",
        "severity": "low",
        "fixed": "0.4.7"
    },
    {
        "uid": "SOL-2016-10",
        "name": "OptimizerStateKnowledgeNotResetForJumpdest",
        "summary": "The optimizer did not properly reset its internal state at jump destinations, which could lead to data corruption.",
        "description": "The optimizer performs symbolic execution at certain stages. At jump destinations, multiple code paths join and thus it has to compute a common state from the incoming edges. Computing this common state was simplified to just use the empty state, but this implementation was not done properly. This bug can cause data corruption.",
        "severity": "medium",
        "introduced": "0.4.5",
        "fixed": "0.4.6",
        "conditions": {
            "optimizer": true
        }
    },
    {
        "uid": "SOL-2016-9",
        "name": "HighOrderByteCleanStorage",
        "summary": "For short types, the high order bytes were not cleaned properly and could overwrite existing data.",
        "description": "Types shorter than 32 bytes are packed together into the same 32 byte storage slot, but storage writes always write 32 bytes. For some types, the higher order bytes were not cleaned properly, which made it sometimes possible to overwrite a variable in storage when writing to another one.",
        "link": "https://blog.soliditylang.org/2016/11/01/security-alert-solidity-variables-can-overwritten-storage/",
        "severity": "high",
        "introduced": "0.1.6",
        "fixed": "0.4.4"
    },
    {
        "uid": "SOL-2016-8",
        "name": "OptimizerStaleKnowledgeAboutSHA3",
        "summary": "The optimizer did not properly reset its knowledge about SHA3 operations resulting in some hashes (also used for storage variable positions) not being calculated correctly.",
        "description": "The optimizer performs symbolic execution in order to save re-evaluating expressions whose value is already known. This knowledge was not properly reset across control flow paths and thus the optimizer sometimes thought that the result of a SHA3 operation is already present on the stack. This could result in data corruption by accessing the wrong storage slot.",
        "severity": "medium",
        "fixed": "0.4.3",
        "conditions": {
            "optimizer": true
        }
    },
    {
        "uid": "SOL-2016-7",
        "name": "LibrariesNotCallableFromPayableFunctions",
        "summary": "Library functions threw an exception when called from a call that received Ether.",
        "description": "Library functions are protected against sending them Ether through a call. Since the DELEGATECALL opcode forwards the information about how much Ether was sent with a call, the library function incorrectly assumed that Ether was sent to the library and threw an exception.",
        "severity": "low",
        "introduced": "0.4.0",
        "fixed": "0.4.2"
    },
    {
        "uid": "SOL-2016-6",
        "name": "SendFailsForZeroEther",
        "summary": "The send function did not provide enough gas to the recipient if no Ether was sent with it.",
        "description": "The recipient of an Ether transfer automatically receives a certain amount of gas from the EVM to handle the transfer. In the case of a zero-transfer, this gas is not provided which causes the recipient to throw an exception.",
        "severity": "low",
        "fixed": "0.4.0"
    },
    {
        "uid": "SOL-2016-5",
        "name": "DynamicAllocationInfiniteLoop",
        "summary": "Dynamic allocation of an empty memory array caused an infinite loop and thus an exception.",
        "description": "Memory arrays can be created provided a length. If this length is zero, code was generated that did not terminate and thus consumed all gas.",
        "severity": "low",
        "fixed": "0.3.6"
    },
    {
        "uid": "SOL-2016-4",
        "name": "OptimizerClearStateOnCodePathJoin",
        "summary": "The optimizer did not properly reset its internal state at jump destinations, which could lead to data corruption.",
        "description": "The optimizer performs symbolic execution at certain stages. At jump destinations, multiple code paths join and thus it has to compute a common state from the incoming edges. Computing this common state was not done correctly. This bug can cause data corruption, but it is probably quite hard to use for targeted attacks.",
        "severity": "low",
        "fixed": "0.3.6",
        "conditions": {
            "optimizer": true
        }
    },
    {
        "uid": "SOL-2016-3",
        "name": "CleanBytesHigherOrderBits",
        "summary": "The higher order bits of short bytesNN types were not cleaned before comparison.",
        "description": "Two variables of type bytesNN were considered different if their higher order bits, which are not part of the actual value, were different. An attacker might use this to reach seemingly unreachable code paths by providing incorrectly formatted input data.",
        "severity": "medium/high",
        "fixed": "0.3.3"
    },
    {
        "uid": "SOL-2016-2",
        "name": "ArrayAccessCleanHigherOrderBits",
        "summary": "Access to array elements for arrays of types with less than 32 bytes did not correctly clean the higher order bits, causing corruption in other array elements.",
        "description": "Multiple elements of an array of values that are shorter than 17 bytes are packed into the same storage slot. Writing to a single element of such an array did not properly clean the higher order bytes and thus could lead to data corruption.",
        "severity": "medium/high",
        "fixed": "0.3.1"
    },
    {
        "uid": "SOL-2016-1",
        "name": "AncientCompiler",
        "summary": "This compiler version is ancient and might contain several undocumented or undiscovered bugs.",
        "description": "The list of bugs is only kept for compiler versions starting from 0.3.0, so older versions might contain undocumented bugs.",
        "severity": "high",
        "fixed": "0.3.0"
    }
]



Solidity v0.5.0 Breaking Changes
This section highlights the main breaking changes introduced in Solidity version 0.5.0, along with the reasoning behind the changes and how to update affected code. For the full list check the release changelog.

Note

Contracts compiled with Solidity v0.5.0 can still interface with contracts and even libraries compiled with older versions without recompiling or redeploying them. Changing the interfaces to include data locations and visibility and mutability specifiers suffices. See the Interoperability With Older Contracts section below.

Semantic Only Changes
This section lists the changes that are semantic-only, thus potentially hiding new and different behavior in existing code.

Signed right shift now uses proper arithmetic shift, i.e. rounding towards negative infinity, instead of rounding towards zero. Signed and unsigned shift will have dedicated opcodes in Constantinople, and are emulated by Solidity for the moment.

The continue statement in a do...while loop now jumps to the condition, which is the common behavior in such cases. It used to jump to the loop body. Thus, if the condition is false, the loop terminates.

The functions .call(), .delegatecall() and .staticcall() do not pad anymore when given a single bytes parameter.

Pure and view functions are now called using the opcode STATICCALL instead of CALL if the EVM version is Byzantium or later. This disallows state changes on the EVM level.

The ABI encoder now properly pads byte arrays and strings from calldata (msg.data and external function parameters) when used in external function calls and in abi.encode. For unpadded encoding, use abi.encodePacked.

The ABI decoder reverts in the beginning of functions and in abi.decode() if passed calldata is too short or points out of bounds. Note that dirty higher order bits are still simply ignored.

Forward all available gas with external function calls starting from Tangerine Whistle.

Semantic and Syntactic Changes
This section highlights changes that affect syntax and semantics.

The functions .call(), .delegatecall(), staticcall(), keccak256(), sha256() and ripemd160() now accept only a single bytes argument. Moreover, the argument is not padded. This was changed to make more explicit and clear how the arguments are concatenated. Change every .call() (and family) to a .call("") and every .call(signature, a, b, c) to use .call(abi.encodeWithSignature(signature, a, b, c)) (the last one only works for value types). Change every keccak256(a, b, c) to keccak256(abi.encodePacked(a, b, c)). Even though it is not a breaking change, it is suggested that developers change x.call(bytes4(keccak256("f(uint256)")), a, b) to x.call(abi.encodeWithSignature("f(uint256)", a, b)).

Functions .call(), .delegatecall() and .staticcall() now return (bool, bytes memory) to provide access to the return data. Change bool success = otherContract.call("f") to (bool success, bytes memory data) = otherContract.call("f").

Solidity now implements C99-style scoping rules for function local variables, that is, variables can only be used after they have been declared and only in the same or nested scopes. Variables declared in the initialization block of a for loop are valid at any point inside the loop.

Explicitness Requirements
This section lists changes where the code now needs to be more explicit. For most of the topics the compiler will provide suggestions.

Explicit function visibility is now mandatory. Add public to every function and constructor, and external to every fallback or interface function that does not specify its visibility already.

Explicit data location for all variables of struct, array or mapping types is now mandatory. This is also applied to function parameters and return variables. For example, change uint[] x = z to uint[] storage x = z, and function f(uint[][] x) to function f(uint[][] memory x) where memory is the data location and might be replaced by storage or calldata accordingly. Note that external functions require parameters with a data location of calldata.

Contract types do not include address members anymore in order to separate the namespaces. Therefore, it is now necessary to explicitly convert values of contract type to addresses before using an address member. Example: if c is a contract, change c.transfer(...) to address(c).transfer(...), and c.balance to address(c).balance.

Explicit conversions between unrelated contract types are now disallowed. You can only convert from a contract type to one of its base or ancestor types. If you are sure that a contract is compatible with the contract type you want to convert to, although it does not inherit from it, you can work around this by converting to address first. Example: if A and B are contract types, B does not inherit from A and b is a contract of type B, you can still convert b to type A using A(address(b)). Note that you still need to watch out for matching payable fallback functions, as explained below.

The address type was split into address and address payable, where only address payable provides the transfer function. An address payable can be directly converted to an address, but the other way around is not allowed. Converting address to address payable is possible via conversion through uint160. If c is a contract, address(c) results in address payable only if c has a payable fallback function. If you use the withdraw pattern, you most likely do not have to change your code because transfer is only used on msg.sender instead of stored addresses and msg.sender is an address payable.

Conversions between bytesX and uintY of different size are now disallowed due to bytesX padding on the right and uintY padding on the left which may cause unexpected conversion results. The size must now be adjusted within the type before the conversion. For example, you can convert a bytes4 (4 bytes) to a uint64 (8 bytes) by first converting the bytes4 variable to bytes8 and then to uint64. You get the opposite padding when converting through uint32. Before v0.5.0 any conversion between bytesX and uintY would go through uint8X. For example uint8(bytes3(0x291807)) would be converted to uint8(uint24(bytes3(0x291807))) (the result is 0x07).

Using msg.value in non-payable functions (or introducing it via a modifier) is disallowed as a security feature. Turn the function into payable or create a new internal function for the program logic that uses msg.value.

For clarity reasons, the command-line interface now requires - if the standard input is used as source.

Deprecated Elements
This section lists changes that deprecate prior features or syntax. Note that many of these changes were already enabled in the experimental mode v0.5.0.

Command-line and JSON Interfaces
The command-line option --formal (used to generate Why3 output for further formal verification) was deprecated and is now removed. A new formal verification module, the SMTChecker, is enabled via pragma experimental SMTChecker;.

The command-line option --julia was renamed to --yul due to the renaming of the intermediate language Julia to Yul.

The --clone-bin and --combined-json clone-bin command-line options were removed.

Remappings with empty prefix are disallowed.

The JSON AST fields constant and payable were removed. The information is now present in the stateMutability field.

The JSON AST field isConstructor of the FunctionDefinition node was replaced by a field called kind which can have the value "constructor", "fallback" or "function".

In unlinked binary hex files, library address placeholders are now the first 36 hex characters of the keccak256 hash of the fully qualified library name, surrounded by $...$. Previously, just the fully qualified library name was used. This reduces the chances of collisions, especially when long paths are used. Binary files now also contain a list of mappings from these placeholders to the fully qualified names.

Constructors
Constructors must now be defined using the constructor keyword.

Calling base constructors without parentheses is now disallowed.

Specifying base constructor arguments multiple times in the same inheritance hierarchy is now disallowed.

Calling a constructor with arguments but with wrong argument count is now disallowed. If you only want to specify an inheritance relation without giving arguments, do not provide parentheses at all.

Functions
Function callcode is now disallowed (in favor of delegatecall). It is still possible to use it via inline assembly.

suicide is now disallowed (in favor of selfdestruct).

sha3 is now disallowed (in favor of keccak256).

throw is now disallowed (in favor of revert, require and assert).

Conversions
Explicit and implicit conversions from decimal literals to bytesXX types is now disallowed.

Explicit and implicit conversions from hex literals to bytesXX types of different size is now disallowed.

Literals and Suffixes
The unit denomination years is now disallowed due to complications and confusions about leap years.

Trailing dots that are not followed by a number are now disallowed.

Combining hex numbers with unit denominations (e.g. 0x1e wei) is now disallowed.

The prefix 0X for hex numbers is disallowed, only 0x is possible.

Variables
Declaring empty structs is now disallowed for clarity.

The var keyword is now disallowed to favor explicitness.

Assignments between tuples with different number of components is now disallowed.

Values for constants that are not compile-time constants are disallowed.

Multi-variable declarations with mismatching number of values are now disallowed.

Uninitialized storage variables are now disallowed.

Empty tuple components are now disallowed.

Detecting cyclic dependencies in variables and structs is limited in recursion to 256.

Fixed-size arrays with a length of zero are now disallowed.

Syntax
Using constant as function state mutability modifier is now disallowed.

Boolean expressions cannot use arithmetic operations.

The unary + operator is now disallowed.

Literals cannot anymore be used with abi.encodePacked without prior conversion to an explicit type.

Empty return statements for functions with one or more return values are now disallowed.

The “loose assembly” syntax is now disallowed entirely, that is, jump labels, jumps and non-functional instructions cannot be used anymore. Use the new while, switch and if constructs instead.

Functions without implementation cannot use modifiers anymore.

Function types with named return values are now disallowed.

Single statement variable declarations inside if/while/for bodies that are not blocks are now disallowed.

New keywords: calldata and constructor.

New reserved keywords: alias, apply, auto, copyof, define, immutable, implements, macro, mutable, override, partial, promise, reference, sealed, sizeof, supports, typedef and unchecked.

Interoperability With Older Contracts
It is still possible to interface with contracts written for Solidity versions prior to v0.5.0 (or the other way around) by defining interfaces for them. Consider you have the following pre-0.5.0 contract already deployed:

open in Remix

// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.4.25;
// This will report a warning until version 0.4.25 of the compiler
// This will not compile after 0.5.0
contract OldContract {
    function someOldFunction(uint8 a) {
        //...
    }
    function anotherOldFunction() constant returns (bool) {
        //...
    }
    // ...
}
This will no longer compile with Solidity v0.5.0. However, you can define a compatible interface for it:

open in Remix

// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.5.0 <0.9.0;
interface OldContract {
    function someOldFunction(uint8 a) external;
    function anotherOldFunction() external returns (bool);
}
Note that we did not declare anotherOldFunction to be view, despite it being declared constant in the original contract. This is due to the fact that starting with Solidity v0.5.0 staticcall is used to call view functions. Prior to v0.5.0 the constant keyword was not enforced, so calling a function declared constant with staticcall may still revert, since the constant function may still attempt to modify storage. Consequently, when defining an interface for older contracts, you should only use view in place of constant in case you are absolutely sure that the function will work with staticcall.

Given the interface defined above, you can now easily use the already deployed pre-0.5.0 contract:

open in Remix

// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.5.0 <0.9.0;

interface OldContract {
    function someOldFunction(uint8 a) external;
    function anotherOldFunction() external returns (bool);
}

contract NewContract {
    function doSomething(OldContract a) public returns (bool) {
        a.someOldFunction(0x42);
        return a.anotherOldFunction();
    }
}
Similarly, pre-0.5.0 libraries can be used by defining the functions of the library without implementation and supplying the address of the pre-0.5.0 library during linking (see Using the Commandline Compiler for how to use the commandline compiler for linking):

open in Remix

// This will not compile after 0.6.0
// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.5.0;

library OldLibrary {
    function someFunction(uint8 a) public returns(bool);
}

contract NewContract {
    function f(uint8 a) public returns (bool) {
        return OldLibrary.someFunction(a);
    }
}
Example
The following example shows a contract and its updated version for Solidity v0.5.0 with some of the changes listed in this section.

Old version:

open in Remix

// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.4.25;
// This will not compile after 0.5.0

contract OtherContract {
    uint x;
    function f(uint y) external {
        x = y;
    }
    function() payable external {}
}

contract Old {
    OtherContract other;
    uint myNumber;

    // Function mutability not provided, not an error.
    function someInteger() internal returns (uint) { return 2; }

    // Function visibility not provided, not an error.
    // Function mutability not provided, not an error.
    function f(uint x) returns (bytes) {
        // Var is fine in this version.
        var z = someInteger();
        x += z;
        // Throw is fine in this version.
        if (x > 100)
            throw;
        bytes memory b = new bytes(x);
        y = -3 >> 1;
        // y == -1 (wrong, should be -2)
        do {
            x += 1;
            if (x > 10) continue;
            // 'Continue' causes an infinite loop.
        } while (x < 11);
        // Call returns only a Bool.
        bool success = address(other).call("f");
        if (!success)
            revert();
        else {
            // Local variables could be declared after their use.
            int y;
        }
        return b;
    }

    // No need for an explicit data location for 'arr'
    function g(uint[] arr, bytes8 x, OtherContract otherContract) public {
        otherContract.transfer(1 ether);

        // Since uint32 (4 bytes) is smaller than bytes8 (8 bytes),
        // the first 4 bytes of x will be lost. This might lead to
        // unexpected behavior since bytesX are right padded.
        uint32 y = uint32(x);
        myNumber += y + msg.value;
    }
}
New version:

open in Remix

// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.5.0;
// This will not compile after 0.6.0

contract OtherContract {
    uint x;
    function f(uint y) external {
        x = y;
    }
    function() payable external {}
}

contract New {
    OtherContract other;
    uint myNumber;

    // Function mutability must be specified.
    function someInteger() internal pure returns (uint) { return 2; }

    // Function visibility must be specified.
    // Function mutability must be specified.
    function f(uint x) public returns (bytes memory) {
        // The type must now be explicitly given.
        uint z = someInteger();
        x += z;
        // Throw is now disallowed.
        require(x <= 100);
        int y = -3 >> 1;
        require(y == -2);
        do {
            x += 1;
            if (x > 10) continue;
            // 'Continue' jumps to the condition below.
        } while (x < 11);

        // Call returns (bool, bytes).
        // Data location must be specified.
        (bool success, bytes memory data) = address(other).call("f");
        if (!success)
            revert();
        return data;
    }

    using AddressMakePayable for address;
    // Data location for 'arr' must be specified
    function g(uint[] memory /* arr */, bytes8 x, OtherContract otherContract, address unknownContract) public payable {
        // 'otherContract.transfer' is not provided.
        // Since the code of 'OtherContract' is known and has the fallback
        // function, address(otherContract) has type 'address payable'.
        address(otherContract).transfer(1 ether);

        // 'unknownContract.transfer' is not provided.
        // 'address(unknownContract).transfer' is not provided
        // since 'address(unknownContract)' is not 'address payable'.
        // If the function takes an 'address' which you want to send
        // funds to, you can convert it to 'address payable' via 'uint160'.
        // Note: This is not recommended and the explicit type
        // 'address payable' should be used whenever possible.
        // To increase clarity, we suggest the use of a library for
        // the conversion (provided after the contract in this example).
        address payable addr = unknownContract.makePayable();
        require(addr.send(1 ether));

        // Since uint32 (4 bytes) is smaller than bytes8 (8 bytes),
        // the conversion is not allowed.
        // We need to convert to a common size first:
        bytes4 x4 = bytes4(x); // Padding happens on the right
        uint32 y = uint32(x4); // Conversion is consistent
        // 'msg.value' cannot be used in a 'non-payable' function.
        // We need to make the function payable
        myNumber += y + msg.value;
    }
}

// We can define a library for explicitly converting ``address``
// to ``address payable`` as a workaround.
library AddressMakePayable {
    function makePayable(address x) internal pure returns (address payable) {
        return address(uint160(x));
    }
}



Solidity v0.6.0 Breaking Changes
This section highlights the main breaking changes introduced in Solidity version 0.6.0, along with the reasoning behind the changes and how to update affected code. For the full list check the release changelog.

Changes the Compiler Might not Warn About
This section lists changes where the behavior of your code might change without the compiler telling you about it.

The resulting type of an exponentiation is the type of the base. It used to be the smallest type that can hold both the type of the base and the type of the exponent, as with symmetric operations. Additionally, signed types are allowed for the base of the exponentiation.

Explicitness Requirements
This section lists changes where the code now needs to be more explicit, but the semantics do not change. For most of the topics the compiler will provide suggestions.

Functions can now only be overridden when they are either marked with the virtual keyword or defined in an interface. Functions without implementation outside an interface have to be marked virtual. When overriding a function or modifier, the new keyword override must be used. When overriding a function or modifier defined in multiple parallel bases, all bases must be listed in parentheses after the keyword like so: override(Base1, Base2).

Member-access to length of arrays is now always read-only, even for storage arrays. It is no longer possible to resize storage arrays by assigning a new value to their length. Use push(), push(value) or pop() instead, or assign a full array, which will of course overwrite the existing content. The reason behind this is to prevent storage collisions of gigantic storage arrays.

The new keyword abstract can be used to mark contracts as abstract. It has to be used if a contract does not implement all its functions. Abstract contracts cannot be created using the new operator, and it is not possible to generate bytecode for them during compilation.

Libraries have to implement all their functions, not only the internal ones.

The names of variables declared in inline assembly may no longer end in _slot or _offset.

Variable declarations in inline assembly may no longer shadow any declaration outside the inline assembly block. If the name contains a dot, its prefix up to the dot may not conflict with any declaration outside the inline assembly block.

In inline assembly, opcodes that do not take arguments are now represented as “built-in functions” instead of standalone identifiers. So gas is now gas().

State variable shadowing is now disallowed. A derived contract can only declare a state variable x, if there is no visible state variable with the same name in any of its bases.

Semantic and Syntactic Changes
This section lists changes where you have to modify your code and it does something else afterwards.

Conversions from external function types to address are now disallowed. Instead external function types have a member called address, similar to the existing selector member.

The function push(value) for dynamic storage arrays does not return the new length anymore (it returns nothing).

The unnamed function commonly referred to as “fallback function” was split up into a new fallback function that is defined using the fallback keyword and a receive ether function defined using the receive keyword.

If present, the receive ether function is called whenever the call data is empty (whether or not ether is received). This function is implicitly payable.

The new fallback function is called when no other function matches (if the receive ether function does not exist then this includes calls with empty call data). You can make this function payable or not. If it is not payable then transactions not matching any other function which send value will revert. You should only need to implement the new fallback function if you are following an upgrade or proxy pattern.

New Features
This section lists things that were not possible prior to Solidity 0.6.0 or were more difficult to achieve.

The try/catch statement allows you to react on failed external calls.

struct and enum types can be declared at file level.

Array slices can be used for calldata arrays, for example abi.decode(msg.data[4:], (uint, uint)) is a low-level way to decode the function call payload.

Natspec supports multiple return parameters in developer documentation, enforcing the same naming check as @param.

Yul and Inline Assembly have a new statement called leave that exits the current function.

Conversions from address to address payable are now possible via payable(x), where x must be of type address.

Interface Changes
This section lists changes that are unrelated to the language itself, but that have an effect on the interfaces of the compiler. These may change the way how you use the compiler on the command-line, how you use its programmable interface, or how you analyze the output produced by it.

New Error Reporter
A new error reporter was introduced, which aims at producing more accessible error messages on the command-line. It is enabled by default, but passing --old-reporter falls back to the deprecated old error reporter.

Metadata Hash Options
The compiler now appends the IPFS hash of the metadata file to the end of the bytecode by default (for details, see documentation on contract metadata). Before 0.6.0, the compiler appended the Swarm hash by default, and in order to still support this behavior, the new command-line option --metadata-hash was introduced. It allows you to select the hash to be produced and appended, by passing either ipfs or swarm as value to the --metadata-hash command-line option. Passing the value none completely removes the hash.

These changes can also be used via the Standard JSON Interface and effect the metadata JSON generated by the compiler.

The recommended way to read the metadata is to read the last two bytes to determine the length of the CBOR encoding and perform a proper decoding on that data block as explained in the metadata section.

Yul Optimizer
Together with the legacy bytecode optimizer, the Yul optimizer is now enabled by default when you call the compiler with --optimize. It can be disabled by calling the compiler with --no-optimize-yul. This mostly affects code that uses ABI coder v2.

C API Changes
The client code that uses the C API of libsolc is now in control of the memory used by the compiler. To make this change consistent, solidity_free was renamed to solidity_reset, the functions solidity_alloc and solidity_free were added and solidity_compile now returns a string that must be explicitly freed via solidity_free().

How to update your code
This section gives detailed instructions on how to update prior code for every breaking change.

Change address(f) to f.address for f being of external function type.

Replace function () external [payable] { ... } by either receive() external payable { ... }, fallback() external [payable] { ... } or both. Prefer using a receive function only, whenever possible.

Change uint length = array.push(value) to array.push(value);. The new length can be accessed via array.length.

Change array.length++ to array.push() to increase, and use pop() to decrease the length of a storage array.

For every named return parameter in a function’s @dev documentation define a @return entry which contains the parameter’s name as the first word. E.g. if you have function f() defined like function f() public returns (uint value) and a @dev annotating it, document its return parameters like so: @return value The return value.. You can mix named and un-named return parameters documentation so long as the notices are in the order they appear in the tuple return type.

Choose unique identifiers for variable declarations in inline assembly that do not conflict with declarations outside the inline assembly block.

Add virtual to every non-interface function you intend to override. Add virtual to all functions without implementation outside interfaces. For single inheritance, add override to every overriding function. For multiple inheritance, add override(A, B, ..), where you list all contracts that define the overridden function in the parentheses. When multiple bases define the same function, the inheriting contract must override all conflicting functions.

In inline assembly, add () to all opcodes that do not otherwise accept an argument. For example, change pc to pc(), and gas to gas().




Solidity v0.7.0 Breaking Changes
This section highlights the main breaking changes introduced in Solidity version 0.7.0, along with the reasoning behind the changes and how to update affected code. For the full list check the release changelog.

Silent Changes of the Semantics
Exponentiation and shifts of literals by non-literals (e.g. 1 << x or 2 ** x) will always use either the type uint256 (for non-negative literals) or int256 (for negative literals) to perform the operation. Previously, the operation was performed in the type of the shift amount / the exponent which can be misleading.

Changes to the Syntax
In external function and contract creation calls, Ether and gas is now specified using a new syntax: x.f{gas: 10000, value: 2 ether}(arg1, arg2). The old syntax – x.f.gas(10000).value(2 ether)(arg1, arg2) – will cause an error.

The global variable now is deprecated, block.timestamp should be used instead. The single identifier now is too generic for a global variable and could give the impression that it changes during transaction processing, whereas block.timestamp correctly reflects the fact that it is just a property of the block.

NatSpec comments on variables are only allowed for public state variables and not for local or internal variables.

The token gwei is a keyword now (used to specify, e.g. 2 gwei as a number) and cannot be used as an identifier.

String literals now can only contain printable ASCII characters and this also includes a variety of escape sequences, such as hexadecimal (\xff) and unicode escapes (\u20ac).

Unicode string literals are supported now to accommodate valid UTF-8 sequences. They are identified with the unicode prefix: unicode"Hello 😃".

State Mutability: The state mutability of functions can now be restricted during inheritance: Functions with default state mutability can be overridden by pure and view functions while view functions can be overridden by pure functions. At the same time, public state variables are considered view and even pure if they are constants.

Inline Assembly
Disallow . in user-defined function and variable names in inline assembly. It is still valid if you use Solidity in Yul-only mode.

Slot and offset of storage pointer variable x are accessed via x.slot and x.offset instead of x_slot and x_offset.

Removal of Unused or Unsafe Features
Mappings outside Storage
If a struct or array contains a mapping, it can only be used in storage. Previously, mapping members were silently skipped in memory, which is confusing and error-prone.

Assignments to structs or arrays in storage does not work if they contain mappings. Previously, mappings were silently skipped during the copy operation, which is misleading and error-prone.

Functions and Events
Visibility (public / internal) is not needed for constructors anymore: To prevent a contract from being created, it can be marked abstract. This makes the visibility concept for constructors obsolete.

Type Checker: Disallow virtual for library functions: Since libraries cannot be inherited from, library functions should not be virtual.

Multiple events with the same name and parameter types in the same inheritance hierarchy are disallowed.

using A for B only affects the contract it is mentioned in. Previously, the effect was inherited. Now, you have to repeat the using statement in all derived contracts that make use of the feature.

Expressions
Shifts by signed types are disallowed. Previously, shifts by negative amounts were allowed, but reverted at runtime.

The finney and szabo denominations are removed. They are rarely used and do not make the actual amount readily visible. Instead, explicit values like 1e20 or the very common gwei can be used.

Declarations
The keyword var cannot be used anymore. Previously, this keyword would parse but result in a type error and a suggestion about which type to use. Now, it results in a parser error.

Interface Changes
JSON AST: Mark hex string literals with kind: "hexString".

JSON AST: Members with value null are removed from JSON output.

NatSpec: Constructors and functions have consistent userdoc output.

How to update your code
This section gives detailed instructions on how to update prior code for every breaking change.

Change x.f.value(...)() to x.f{value: ...}(). Similarly (new C).value(...)() to new C{value: ...}() and x.f.gas(...).value(...)() to x.f{gas: ..., value: ...}().

Change now to block.timestamp.

Change types of right operand in shift operators to unsigned types. For example change x >> (256 - y) to x >> uint(256 - y).

Repeat the using A for B statements in all derived contracts if needed.

Remove the public keyword from every constructor.

Remove the internal keyword from every constructor and add abstract to the contract (if not already present).

Change _slot and _offset suffixes in inline assembly to .slot and .offset, respectively.




Solidity v0.8.0 Breaking Changes
This section highlights the main breaking changes introduced in Solidity version 0.8.0. For the full list check the release changelog.

Silent Changes of the Semantics
This section lists changes where existing code changes its behavior without the compiler notifying you about it.

Arithmetic operations revert on underflow and overflow. You can use unchecked { ... } to use the previous wrapping behavior.

Checks for overflow are very common, so we made them the default to increase readability of code, even if it comes at a slight increase of gas costs.

ABI coder v2 is activated by default.

You can choose to use the old behavior using pragma abicoder v1;. The pragma pragma experimental ABIEncoderV2; is still valid, but it is deprecated and has no effect. If you want to be explicit, please use pragma abicoder v2; instead.

Note that ABI coder v2 supports more types than v1 and performs more sanity checks on the inputs. ABI coder v2 makes some function calls more expensive and it can also make contract calls revert that did not revert with ABI coder v1 when they contain data that does not conform to the parameter types.

Exponentiation is right associative, i.e., the expression a**b**c is parsed as a**(b**c). Before 0.8.0, it was parsed as (a**b)**c.

This is the common way to parse the exponentiation operator.

Failing assertions and other internal checks like division by zero or arithmetic overflow do not use the invalid opcode but instead the revert opcode. More specifically, they will use error data equal to a function call to Panic(uint256) with an error code specific to the circumstances.

This will save gas on errors while it still allows static analysis tools to distinguish these situations from a revert on invalid input, like a failing require.

If a byte array in storage is accessed whose length is encoded incorrectly, a panic is caused. A contract cannot get into this situation unless inline assembly is used to modify the raw representation of storage byte arrays.

If constants are used in array length expressions, previous versions of Solidity would use arbitrary precision in all branches of the evaluation tree. Now, if constant variables are used as intermediate expressions, their values will be properly rounded in the same way as when they are used in run-time expressions.

The type byte has been removed. It was an alias of bytes1.

New Restrictions
This section lists changes that might cause existing contracts to not compile anymore.

There are new restrictions related to explicit conversions of literals. The previous behavior in the following cases was likely ambiguous:

Explicit conversions from negative literals and literals larger than type(uint160).max to address are disallowed.

Explicit conversions between literals and an integer type T are only allowed if the literal lies between type(T).min and type(T).max. In particular, replace usages of uint(-1) with type(uint).max.

Explicit conversions between literals and enums are only allowed if the literal can represent a value in the enum.

Explicit conversions between literals and address type (e.g. address(literal)) have the type address instead of address payable. One can get a payable address type by using an explicit conversion, i.e., payable(literal).

Address literals have the type address instead of address payable. They can be converted to address payable by using an explicit conversion, e.g. payable(0xdCad3a6d3569DF655070DEd06cb7A1b2Ccd1D3AF).

There are new restrictions on explicit type conversions. The conversion is only allowed when there is at most one change in sign, width or type-category (int, address, bytesNN, etc.). To perform multiple changes, use multiple conversions.

Let us use the notation T(S) to denote the explicit conversion T(x), where, T and S are types, and x is any arbitrary variable of type S. An example of such a disallowed conversion would be uint16(int8) since it changes both width (8 bits to 16 bits) and sign (signed integer to unsigned integer). In order to do the conversion, one has to go through an intermediate type. In the previous example, this would be uint16(uint8(int8)) or uint16(int16(int8)). Note that the two ways to convert will produce different results e.g., for -1. The following are some examples of conversions that are disallowed by this rule.

address(uint) and uint(address): converting both type-category and width. Replace this by address(uint160(uint)) and uint(uint160(address)) respectively.

payable(uint160), payable(bytes20) and payable(integer-literal): converting both type-category and state-mutability. Replace this by payable(address(uint160)), payable(address(bytes20)) and payable(address(integer-literal)) respectively. Note that payable(0) is valid and is an exception to the rule.

int80(bytes10) and bytes10(int80): converting both type-category and sign. Replace this by int80(uint80(bytes10)) and bytes10(uint80(int80) respectively.

Contract(uint): converting both type-category and width. Replace this by Contract(address(uint160(uint))).

These conversions were disallowed to avoid ambiguity. For example, in the expression uint16 x = uint16(int8(-1)), the value of x would depend on whether the sign or the width conversion was applied first.

Function call options can only be given once, i.e. c.f{gas: 10000}{value: 1}() is invalid and has to be changed to c.f{gas: 10000, value: 1}().

The global functions log0, log1, log2, log3 and log4 have been removed.

These are low-level functions that were largely unused. Their behavior can be accessed from inline assembly.

enum definitions cannot contain more than 256 members.

This will make it safe to assume that the underlying type in the ABI is always uint8.

Declarations with the name this, super and _ are disallowed, with the exception of public functions and events. The exception is to make it possible to declare interfaces of contracts implemented in languages other than Solidity that do permit such function names.

Remove support for the \b, \f, and \v escape sequences in code. They can still be inserted via hexadecimal escapes, e.g. \x08, \x0c, and \x0b, respectively.

The global variables tx.origin and msg.sender have the type address instead of address payable. One can convert them into address payable by using an explicit conversion, i.e., payable(tx.origin) or payable(msg.sender).

This change was done since the compiler cannot determine whether or not these addresses are payable or not, so it now requires an explicit conversion to make this requirement visible.

Explicit conversion into address type always returns a non-payable address type. In particular, the following explicit conversions have the type address instead of address payable:

address(u) where u is a variable of type uint160. One can convert u into the type address payable by using two explicit conversions, i.e., payable(address(u)).

address(b) where b is a variable of type bytes20. One can convert b into the type address payable by using two explicit conversions, i.e., payable(address(b)).

address(c) where c is a contract. Previously, the return type of this conversion depended on whether the contract can receive Ether (either by having a receive function or a payable fallback function). The conversion payable(c) has the type address payable and is only allowed when the contract c can receive Ether. In general, one can always convert c into the type address payable by using the following explicit conversion: payable(address(c)). Note that address(this) falls under the same category as address(c) and the same rules apply for it.

The chainid builtin in inline assembly is now considered view instead of pure.

Unary negation cannot be used on unsigned integers anymore, only on signed integers.

Interface Changes
The output of --combined-json has changed: JSON fields abi, devdoc, userdoc and storage-layout are sub-objects now. Before 0.8.0 they used to be serialised as strings.

The “legacy AST” has been removed (--ast-json on the commandline interface and legacyAST for standard JSON). Use the “compact AST” (--ast-compact-json resp. AST) as replacement.

The old error reporter (--old-reporter) has been removed.

How to update your code
If you rely on wrapping arithmetic, surround each operation with unchecked { ... }.

Optional: If you use SafeMath or a similar library, change x.add(y) to x + y, x.mul(y) to x * y etc.

Add pragma abicoder v1; if you want to stay with the old ABI coder.

Optionally remove pragma experimental ABIEncoderV2 or pragma abicoder v2 since it is redundant.

Change byte to bytes1.

Add intermediate explicit type conversions if required.

Combine c.f{gas: 10000}{value: 1}() to c.f{gas: 10000, value: 1}().

Change msg.sender.transfer(x) to payable(msg.sender).transfer(x) or use a stored variable of address payable type.

Change x**y**z to (x**y)**z.

Use inline assembly as a replacement for log0, …, log4.

Negate unsigned integers by subtracting them from the maximum value of the type and adding 1 (e.g. type(uint256).max - x + 1, while ensuring that x is not zero)

