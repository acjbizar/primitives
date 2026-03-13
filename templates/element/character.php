<?php
declare(strict_types=1);

/**
 * Usage:
 * <?= $this->element('character', ['character' => 'A']) ?>
 */

$character = (string)($character ?? '');

if ($character === '') {
    echo '<!-- character.php: missing character -->';
    return;
}

$cp = mb_ord($character, 'UTF-8');
$filename = sprintf('character-u%04x.svg', $cp);
$path = ROOT . DS . 'src' . DS . 'svg' . DS . $filename;

if (is_file($path)) {
    echo file_get_contents($path);
} else {
    echo '<!-- character.php: missing SVG for ' . h($character) . ' -->';
}