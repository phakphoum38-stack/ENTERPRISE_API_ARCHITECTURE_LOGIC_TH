<?php

use Illuminate\Http\JsonResponse;
use Illuminate\Support\Facades\Route;
use ResearchOS\Platform\Http\PlatformController;
use ResearchOS\Platform\Http\VersionController;

$health = static fn (): JsonResponse => response()->json([
    'service' => 'research-os-laravel-platform',
    'status' => 'ok',
    'contract_version' => '1.0.0',
]);

$ready = static fn (): JsonResponse => response()->json([
    'service' => 'research-os-laravel-platform',
    'status' => 'ready',
    'contract_version' => '1.0.0',
]);

Route::get('/health', $health);
Route::get('/ready', $ready);

Route::prefix('v1')->group(function () use ($health, $ready): void {
    Route::get('/health', $health);
    Route::get('/ready', $ready);
    Route::get('/platform/operations', [PlatformController::class, 'operations']);
    Route::post('/platform/tools', [PlatformController::class, 'tool']);
    Route::post('/platform/control', [PlatformController::class, 'control']);
    Route::post('/platform/version/check', [VersionController::class, 'check']);
});
